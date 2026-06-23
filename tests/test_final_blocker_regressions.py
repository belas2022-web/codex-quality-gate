from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from codex_quality_gate.chat_bridge.sanitizer import (
    redact_nested,
    redact_secret_text,
    sanitize_api_response,
)
from codex_quality_gate.core.errors import PolicyViolationError, SecurityVerificationError
from codex_quality_gate.dashboard.app import create_app
from codex_quality_gate.dashboard.schemas import DashboardConfig
from codex_quality_gate.database.repository import Repository
from codex_quality_gate.database.sqlite import connect
from codex_quality_gate.policies.risk_policy import RiskPolicy
from codex_quality_gate.updates.rollback import rollback_file

SECRET = "secret-token-" + "1234567890"
SLACK_TOKEN_FIXTURE = "xox" + "b-" + "123456789012-" + "123456789012-" + "abcdefghijklmnop"


def _client_with_config(tmp_path: Path, payload: dict[str, object]) -> TestClient:
    config = tmp_path / "config.json"
    config.write_text(json.dumps(payload), encoding="utf-8")
    return TestClient(create_app(DashboardConfig(config_path=config)))


def test_sources_endpoint_redacts_secret_in_last_error(tmp_path: Path) -> None:
    client = _client_with_config(
        tmp_path,
        {
            "updates": {
                "sources": [
                    {
                        "name": "private-source",
                        "type": "github_pages",
                        "last_error": f"upstream failed with {SECRET}",
                    }
                ]
            }
        },
    )

    response = client.get("/api/sources")

    assert response.status_code == 200
    assert SECRET not in response.text
    assert "[REDACTED]" in response.text


def test_chats_endpoint_redacts_secret_in_last_error_and_nested_config(tmp_path: Path) -> None:
    client = _client_with_config(
        tmp_path,
        {
            "chat_bridge": {
                "connectors": [
                    {
                        "name": "slack-prod",
                        "type": "slack",
                        "token_env": SECRET,
                        "config_json": {"authorization": f"Bearer {SECRET}"},
                        "last_error": f"token failure {SECRET}",
                    }
                ]
            }
        },
    )

    response = client.get("/api/chats")

    assert response.status_code == 200
    assert SECRET not in response.text
    assert "[REDACTED]" in response.text


def test_audit_endpoint_redacts_secret_details(tmp_path: Path) -> None:
    database = tmp_path / "dashboard.sqlite"
    repo = Repository(connect(database))
    repo.save_audit_event("source.sync.failed", {"details": f"request failed with {SECRET}"})
    client = TestClient(create_app(DashboardConfig(database_path=database)))

    response = client.get("/api/audit")

    assert response.status_code == 200
    assert SECRET not in response.text
    assert "[REDACTED]" in response.text


@pytest.mark.parametrize(
    ("raw", "secret"),
    [
        (f"request failed with {SECRET}", SECRET),
        (
            "Authorization: Bearer ghp_abcdefghijklmnopqrstuvwxyz123456",
            "ghp_abcdefghijklmnopqrstuvwxyz123456",
        ),
        (
            f"slack token {SLACK_TOKEN_FIXTURE}",
            SLACK_TOKEN_FIXTURE,
        ),
        (
            "jwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.signature123",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.signature123",
        ),
        ("postgres://user:password@example.com/db", "password"),
    ],
)
def test_sanitizer_redacts_token_like_values(raw: str, secret: str) -> None:
    redacted = redact_secret_text(raw)

    assert secret not in redacted
    assert "[REDACTED]" in redacted


def test_sanitizer_recursively_redacts_nested_api_response() -> None:
    payload = {
        "source": {"last_error": f"failed with {SECRET}"},
        "tokens": [f"Bearer {SECRET}", {"api_key": "sk_test_1234567890abcdef"}],
    }

    redacted = sanitize_api_response(payload)

    assert SECRET not in json.dumps(redacted)
    assert "sk_test_1234567890abcdef" not in json.dumps(redacted)
    assert redact_nested(payload) == redacted


@pytest.mark.parametrize(
    "path",
    [
        "src/codex_quality_gate/updates/updater.py",
        "src/codex_quality_gate/update_sources/github_releases.py",
        "src/codex_quality_gate/dashboard/api.py",
        "src/codex_quality_gate/dashboard/auth.py",
        "src/codex_quality_gate/chat_bridge/slack.py",
        "src/codex_quality_gate/security/tokens.py",
        "src/codex_quality_gate/auth/routes.py",
        "src/codex_quality_gate/policies/risk_policy.py",
        ".github/workflows/quality.yml",
        "package.json",
        "pyproject.toml",
        "Dockerfile",
        "docker-compose.yml",
        "migrations/001_init.sql",
    ],
)
def test_risk_policy_requires_review_for_nested_sensitive_paths(path: str) -> None:
    assert RiskPolicy().requires_review(path)


def test_risk_policy_normalizes_windows_backslashes() -> None:
    assert RiskPolicy().requires_review(r"src\codex_quality_gate\dashboard\api.py")


def test_git_diff_policy_flags_nested_sensitive_paths() -> None:
    decision = RiskPolicy().validate_diff(
        "diff --git a/src/codex_quality_gate/updates/updater.py "
        "b/src/codex_quality_gate/updates/updater.py\n"
        "--- a/src/codex_quality_gate/updates/updater.py\n"
        "+++ b/src/codex_quality_gate/updates/updater.py\n"
        "+change\n"
    )

    assert decision.review_required


@pytest.mark.parametrize("path", [".env", "private_keys/prod.pem", "secrets/api.json"])
def test_risk_policy_blocks_secret_bearing_paths(path: str) -> None:
    with pytest.raises(PolicyViolationError):
        RiskPolicy().validate_diff(f"+++ b/{path}\n+secret=value\n")


def test_rollback_rejects_absolute_destination(tmp_path: Path) -> None:
    backup = tmp_path / "backups" / "rules.bak"
    backup.parent.mkdir()
    backup.write_bytes(b"backup")

    with pytest.raises(SecurityVerificationError):
        rollback_file(tmp_path / "outside.json", "backups/rules.bak", base_dir=tmp_path / "rules")


def test_rollback_rejects_path_traversal_destination(tmp_path: Path) -> None:
    backup = tmp_path / "backups" / "rules.bak"
    backup.parent.mkdir()
    backup.write_bytes(b"backup")

    with pytest.raises(SecurityVerificationError):
        rollback_file("../outside.json", "backups/rules.bak", base_dir=tmp_path / "rules")


def test_rollback_allows_source_and_destination_inside_safe_base(tmp_path: Path) -> None:
    backup = tmp_path / "rules" / "backups" / "rules.bak"
    backup.parent.mkdir(parents=True)
    backup.write_bytes(b"safe")

    rollback_file("active/rules.json", "backups/rules.bak", base_dir=tmp_path / "rules")

    assert (tmp_path / "rules" / "active" / "rules.json").read_bytes() == b"safe"


def test_frontend_package_has_real_lint_script() -> None:
    payload = json.loads(Path("frontend/package.json").read_text(encoding="utf-8"))
    lint_script = payload.get("scripts", {}).get("lint")

    assert isinstance(lint_script, str)
    assert lint_script
    assert "echo" not in lint_script
    assert "typecheck" not in lint_script
