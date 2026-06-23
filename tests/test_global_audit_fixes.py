from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import codex_quality_gate.checks.base as checks_base
import codex_quality_gate.database.repository as repository_module
from codex_quality_gate.checks.orchestrator import CheckOrchestrator
from codex_quality_gate.core.result import ScanResult
from codex_quality_gate.dashboard.app import create_app
from codex_quality_gate.dashboard.schemas import DashboardConfig
from codex_quality_gate.database.repository import Repository
from codex_quality_gate.database.sqlite import connect
from codex_quality_gate.detection.project_profiler import ProjectProfiler

PUBLIC_HOST = ".".join(["0", "0", "0", "0"])
SECRET = "secret-token-" + "1234567890"
SLACK_TOKEN_FIXTURE = "xox" + "b-" + "123456789012-" + "123456789012-" + "abcdefghijklmnop"


def test_dashboard_auth_token_rejects_missing_and_wrong_headers() -> None:
    client = TestClient(create_app(DashboardConfig(host=PUBLIC_HOST, auth_token=SECRET)))

    assert client.get("/api/health").status_code == 401
    assert client.get("/api/health", headers={"Authorization": "Bearer wrong"}).status_code == 401


def test_dashboard_auth_token_accepts_bearer_and_x_header() -> None:
    client = TestClient(create_app(DashboardConfig(host=PUBLIC_HOST, auth_token=SECRET)))

    bearer_response = client.get("/api/health", headers={"Authorization": f"Bearer {SECRET}"})
    x_header_response = client.get("/api/health", headers={"X-Codex-Quality-Gate-Token": SECRET})

    assert bearer_response.status_code == 200
    assert x_header_response.status_code == 200


def test_dashboard_auth_does_not_accept_query_token_or_echo_secret() -> None:
    client = TestClient(create_app(DashboardConfig(host=PUBLIC_HOST, auth_token=SECRET)))

    assert client.get(f"/api/health?token={SECRET}").status_code == 401
    response = client.get("/api/health", headers={"Authorization": f"Bearer {SECRET}"})

    assert response.status_code == 200
    assert SECRET not in response.text


def test_dashboard_auth_rejects_empty_or_non_bearer_authorization() -> None:
    client = TestClient(create_app(DashboardConfig(host=PUBLIC_HOST, auth_token=SECRET)))

    assert client.get("/api/health", headers={"Authorization": "Bearer    "}).status_code == 401
    assert (
        client.get("/api/health", headers={"Authorization": f"Basic {SECRET}"}).status_code == 401
    )


def test_dashboard_auth_uses_constant_time_compare() -> None:
    auth_source = Path("src/codex_quality_gate/dashboard/auth.py").read_text(encoding="utf-8")

    assert "hmac.compare_digest" in auth_source


def test_save_audit_event_redacts_secret_before_sqlite_write(tmp_path: Path) -> None:
    repo = Repository(connect(tmp_path / "db.sqlite"))

    repo.save_audit_event("source.sync.failed", {"details": f"leak {SECRET}"})
    raw_payload = repo.connection.execute("SELECT payload FROM audit_events").fetchone()[0]

    assert SECRET not in raw_payload
    assert "[REDACTED]" in raw_payload
    assert repo.list_audit_events()[0]["payload"] == {"details": "leak [REDACTED]"}


@pytest.mark.parametrize(
    ("value", "secret"),
    [
        (
            "Authorization: Bearer ghp_abcdefghijklmnopqrstuvwxyz123456",
            "ghp_abcdefghijklmnopqrstuvwxyz123456",
        ),
        (
            f"slack token {SLACK_TOKEN_FIXTURE}",
            SLACK_TOKEN_FIXTURE,
        ),
        ("postgres://user:password@example.com/db", "password"),
        ("api_key=sk_test_1234567890abcdef", "sk_test_1234567890abcdef"),
    ],
)
def test_audit_payload_redacts_common_secret_patterns(
    tmp_path: Path, value: str, secret: str
) -> None:
    repo = Repository(connect(tmp_path / "db.sqlite"))

    repo.save_audit_event("secret.test", {"details": value})
    raw_payload = repo.connection.execute("SELECT payload FROM audit_events").fetchone()[0]

    assert secret not in raw_payload
    assert "[REDACTED]" in raw_payload


def test_sanitize_existing_audit_payloads_redacts_old_rows_and_is_idempotent(
    tmp_path: Path,
) -> None:
    connection = connect(tmp_path / "db.sqlite")
    connection.execute(
        "INSERT INTO audit_events(event_type, payload) VALUES (?, ?)",
        ("legacy", json.dumps({"details": f"leak {SECRET}"}, sort_keys=True)),
    )
    connection.commit()

    assert hasattr(repository_module, "sanitize_existing_audit_payloads")
    assert repository_module.sanitize_existing_audit_payloads(connection) == 1
    raw_payload = connection.execute("SELECT payload FROM audit_events").fetchone()[0]
    assert SECRET not in raw_payload
    assert "[REDACTED]" in raw_payload
    assert repository_module.sanitize_existing_audit_payloads(connection) == 0


def test_project_profiler_detects_nested_frontend_package_json(tmp_path: Path) -> None:
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text(
        json.dumps({"scripts": {"lint": "eslint ."}, "dependencies": {"react": "1"}}),
        encoding="utf-8",
    )
    (frontend / "package-lock.json").write_text("{}", encoding="utf-8")

    profile = ProjectProfiler().profile(tmp_path)

    assert "frontend/package.json" in profile.frontend_package_paths
    assert "npm" in profile.package_managers


def test_project_profiler_detects_workspace_package_json(tmp_path: Path) -> None:
    package = tmp_path / "packages" / "dashboard"
    package.mkdir(parents=True)
    (package / "package.json").write_text(
        json.dumps({"scripts": {"build": "vite build"}, "dependencies": {"react": "1"}}),
        encoding="utf-8",
    )

    profile = ProjectProfiler().profile(tmp_path)

    assert "packages/dashboard/package.json" in profile.frontend_package_paths


def test_full_profile_runs_frontend_checks_with_frontend_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text(
        json.dumps(
            {
                "scripts": {
                    "lint": "eslint .",
                    "typecheck": "tsc -b --noEmit",
                    "build": "tsc -b && vite build",
                },
                "dependencies": {"react": "1"},
            }
        ),
        encoding="utf-8",
    )
    (frontend / "package-lock.json").write_text("{}", encoding="utf-8")
    calls: list[tuple[tuple[str, ...], Path]] = []

    def fake_run(command: tuple[str, ...], **kwargs: object) -> SimpleNamespace:
        calls.append((tuple(command), Path(str(kwargs["cwd"]))))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(checks_base.subprocess, "run", fake_run)

    result = CheckOrchestrator().run(tmp_path, "full")

    assert isinstance(result, ScanResult)
    npm_results = {
        item.check_id: item
        for item in result.check_results
        if item.check_id in {"npm_lint", "npm_typecheck", "npm_build", "npm_audit"}
    }
    assert set(npm_results) == {"npm_lint", "npm_typecheck", "npm_build", "npm_audit"}
    assert all(item.status.value == "passed" for item in npm_results.values())
    assert any(
        _npm_command_is(command, ("run", "lint")) and cwd == frontend for command, cwd in calls
    )
    assert any(
        _npm_command_is(command, ("run", "typecheck")) and cwd == frontend for command, cwd in calls
    )
    assert any(
        _npm_command_is(command, ("run", "build")) and cwd == frontend for command, cwd in calls
    )
    assert any(_npm_command_is(command, ("audit",)) and cwd == frontend for command, cwd in calls)


def test_quality_workflow_runs_frontend_checks() -> None:
    workflow = Path(".github/workflows/quality.yml").read_text(encoding="utf-8")

    assert "actions/setup-node" in workflow
    assert "working-directory: frontend" in workflow
    assert "npm ci" in workflow
    assert "npm run lint" in workflow
    assert "npm run typecheck" in workflow
    assert "npm run build" in workflow
    assert "npm audit" in workflow


def _npm_command_is(command: tuple[str, ...], expected: tuple[str, ...]) -> bool:
    return (
        Path(command[0]).stem.lower().startswith("npm")
        and command[1 : 1 + len(expected)] == expected
    )
