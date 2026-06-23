from __future__ import annotations

import base64
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from typer.testing import CliRunner

import codex_quality_gate.checks.orchestrator as orchestrator_module
import codex_quality_gate.cli as cli_module
from codex_quality_gate.core.errors import SecurityVerificationError
from codex_quality_gate.dashboard.app import create_app
from codex_quality_gate.dashboard.schemas import DashboardConfig
from codex_quality_gate.projects.registry import ProjectRegistry
from codex_quality_gate.rules.rule_engine import RuleEngine
from codex_quality_gate.updates.hashing import sha256_bytes
from codex_quality_gate.updates.models import UpdateManifest
from codex_quality_gate.updates.update_client import UpdateClient
from codex_quality_gate.updates.updater import Updater

runner = CliRunner()


def _signed_manifest(payload: bytes = b"rules") -> tuple[str, UpdateManifest]:
    private = Ed25519PrivateKey.generate()
    public_key = base64.b64encode(private.public_key().public_bytes_raw()).decode()
    signature = base64.b64encode(private.sign(payload)).decode()
    return public_key, UpdateManifest(
        "1.0.0",
        "2026-06-22T00:00:00Z",
        "2999-01-01T00:00:00Z",
        "https://good.example/rules.json",
        sha256_bytes(payload),
        signature,
    )


def test_semgrep_tool_resolution_finds_venv_windows_path(tmp_path: Path) -> None:
    semgrep = tmp_path / ".venv" / "Scripts" / "semgrep.exe"
    semgrep.parent.mkdir(parents=True)
    semgrep.write_text("", encoding="utf-8")

    assert hasattr(orchestrator_module, "resolve_tool_command")
    command = orchestrator_module.resolve_tool_command(tmp_path, "semgrep", "semgrep")

    assert command[0] == str(semgrep)


def test_semgrep_tool_resolution_finds_venv_unix_path(tmp_path: Path) -> None:
    semgrep = tmp_path / ".venv" / "bin" / "semgrep"
    semgrep.parent.mkdir(parents=True)
    semgrep.write_text("", encoding="utf-8")

    assert hasattr(orchestrator_module, "resolve_tool_command")
    command = orchestrator_module.resolve_tool_command(tmp_path, "semgrep", "semgrep")

    assert command[0] == str(semgrep)


def test_semgrep_tool_resolution_finds_current_env_script(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scripts_dir = tmp_path / "runner-venv" / "Scripts"
    python = scripts_dir / "python.exe"
    semgrep = scripts_dir / "semgrep.exe"
    scripts_dir.mkdir(parents=True)
    python.write_text("", encoding="utf-8")
    semgrep.write_text("", encoding="utf-8")
    project_root = tmp_path / "external-project"
    project_root.mkdir()

    monkeypatch.setattr(orchestrator_module.sys, "executable", str(python))

    command = orchestrator_module.resolve_tool_command(project_root, "semgrep", "semgrep")

    assert command[0] == str(semgrep)


def test_invalid_check_profile_exits_2_without_traceback(tmp_path: Path) -> None:
    result = runner.invoke(cli_module.app, ["check", str(tmp_path), "--profile", "missing"])

    assert result.exit_code == 2
    assert "Traceback" not in result.output


class RedirectResponse:
    def __init__(
        self,
        status_code: int,
        url: str,
        *,
        location: str = "",
        content: bytes = b"",
        content_length: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.url = url
        self.headers: dict[str, str] = {}
        if location:
            self.headers["Location"] = location
        if content_length is not None:
            self.headers["Content-Length"] = content_length
        self.content = content

    def raise_for_status(self) -> None:
        return None

    def iter_content(self, chunk_size: int = 65536):
        _ = chunk_size
        yield self.content


class RedirectSession:
    def __init__(self, responses: list[RedirectResponse]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def get(self, url: str, **kwargs: object) -> RedirectResponse:
        self.calls.append({"url": url, **kwargs})
        return self.responses.pop(0)


def test_update_fetch_rejects_redirect_to_untrusted_domain() -> None:
    session = RedirectSession(
        [
            RedirectResponse(
                302,
                "https://good.example/rules.json",
                location="https://evil.example/rules.json",
            )
        ]
    )

    with pytest.raises(SecurityVerificationError):
        UpdateClient(session).get_bytes(  # type: ignore[arg-type]
            "https://good.example/rules.json",
            allowed_domains=["good.example"],
        )


def test_update_fetch_rejects_oversized_content_length() -> None:
    session = RedirectSession(
        [
            RedirectResponse(
                200,
                "https://good.example/rules.json",
                content=b"x",
                content_length="101",
            )
        ]
    )

    with pytest.raises(SecurityVerificationError):
        UpdateClient(session).get_bytes(  # type: ignore[arg-type]
            "https://good.example/rules.json",
            allowed_domains=["good.example"],
            max_size_bytes=100,
        )


def test_updater_rejects_absolute_target_path(tmp_path: Path) -> None:
    payload = b"rules"
    public_key, manifest = _signed_manifest(payload)

    class Client:
        def get_bytes(
            self,
            _url: str,
            *,
            allowed_domains: list[str],
            max_size_bytes: int,
        ) -> bytes:
            assert allowed_domains == ["good.example"]
            assert max_size_bytes > 0
            return payload

    updater = Updater(["good.example"], public_key, Client(), data_dir=tmp_path)  # type: ignore[arg-type]

    with pytest.raises(SecurityVerificationError):
        updater.apply_rules(manifest, tmp_path / "outside.json", "update.lock")


def test_updater_rejects_lock_path_traversal(tmp_path: Path) -> None:
    payload = b"rules"
    public_key, manifest = _signed_manifest(payload)

    class Client:
        def get_bytes(
            self,
            _url: str,
            *,
            allowed_domains: list[str],
            max_size_bytes: int,
        ) -> bytes:
            assert allowed_domains == ["good.example"]
            assert max_size_bytes > 0
            return payload

    updater = Updater(["good.example"], public_key, Client(), data_dir=tmp_path)  # type: ignore[arg-type]

    with pytest.raises(SecurityVerificationError):
        updater.apply_rules(manifest, "rules.json", "../update.lock")


def test_dashboard_command_calls_uvicorn_run(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(app: object, *, host: str, port: int) -> None:
        calls.append({"app": app, "host": host, "port": port})

    monkeypatch.setattr(cli_module, "uvicorn", SimpleNamespace(run=fake_run), raising=False)

    result = runner.invoke(cli_module.app, ["dashboard"])

    assert result.exit_code == 0
    assert calls and calls[0]["host"] == "127.0.0.1" and calls[0]["port"] == 8765


def test_dashboard_sources_read_configured_sources(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "updates": {
                    "sources": [
                        {
                            "name": "private-source",
                            "type": "github_pages",
                            "enabled": False,
                            "token": "secret-value",
                        }
                    ]
                },
                "chat_bridge": {"connectors": []},
            }
        ),
        encoding="utf-8",
    )

    app = create_app(DashboardConfig(config_path=config))
    payload = app.state.repository
    _ = payload
    response = __import__("fastapi.testclient").testclient.TestClient(app).get("/api/sources")

    assert response.json() == [
        {
            "name": "private-source",
            "type": "github_pages",
            "enabled": False,
            "status": "configured",
            "last_sync_at": None,
            "last_error": None,
            "secrets_exposed": False,
        }
    ]
    assert "secret-value" not in response.text


def test_project_scan_returns_1_on_security_finding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "bad.py").write_text("eval(x)\n", encoding="utf-8")
    ProjectRegistry(cli_module.registry_path()).add("demo", project_dir)

    result = runner.invoke(cli_module.app, ["project", "scan", "demo"])

    assert result.exit_code == 1
    assert "SEC-PY-EVAL" in result.output


def test_frontend_pages_are_reachable_from_app() -> None:
    app_tsx = Path("frontend/src/App.tsx").read_text(encoding="utf-8")

    for page in (
        "Projects",
        "ProjectDetails",
        "Findings",
        "Runs",
        "Updates",
        "Rules",
        "Sources",
        "ChatBridge",
        "AuditLog",
        "Settings",
    ):
        assert f"import {page}" in app_tsx
    assert "setPage(" in app_tsx


def test_semgrep_rules_are_narrowed_for_self_use() -> None:
    payload = yaml.safe_load(Path("src/codex_quality_gate/data/default_semgrep.yml").read_text())
    rules = {rule["id"]: rule for rule in payload["rules"]}

    requests_rule = json.dumps(rules["cqg.python.requests-no-timeout"])
    updater_rule = json.dumps(rules["cqg.updater.auto-execute"])
    assert "requests.$METHOD(...)" not in requests_rule
    assert "metavariable-regex" in updater_rule
    assert "download|artifact|payload" in updater_rule


def test_open_redirect_rule_does_not_flag_safe_update_validation() -> None:
    engine = RuleEngine()

    unsafe = engine.scan_text("view.py", "return redirect(next_url)\n")
    safe = engine.scan_text(
        "update_client.py",
        "_validate_redirect(current_url, next_url, allowed_domains)\n"
        "redirect_chain.append(next_url)\n"
        "validate_no_redirect_to_untrusted_domain(current_url, final_url, allowed_domains)\n",
    )

    assert [finding.rule_id for finding in unsafe] == ["SEC-OPEN-REDIRECT"]
    assert safe == []
