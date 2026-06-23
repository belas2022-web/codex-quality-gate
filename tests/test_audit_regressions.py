from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from codex_quality_gate.chat_bridge.router import parse_chat_command
from codex_quality_gate.checks.orchestrator import CheckOrchestrator
from codex_quality_gate.cli import app
from codex_quality_gate.constants import DEFAULT_ED25519_PUBLIC_KEY_BASE64, VERSION
from codex_quality_gate.core.errors import PolicyViolationError, SecurityVerificationError
from codex_quality_gate.policies.autofix_policy import AutofixPolicy

REQUIRED_RULE_IDS = {
    "SEC-PY-EVAL",
    "SEC-PY-EXEC",
    "SEC-PY-SHELL-TRUE",
    "SEC-PY-PICKLE-LOADS",
    "SEC-PY-YAML-LOAD",
    "SEC-PY-VERIFY-FALSE",
    "SEC-PY-REQUESTS-NO-TIMEOUT",
    "SEC-PY-HARDCODED-SECRET",
    "SEC-JS-EVAL",
    "SEC-JS-INNERHTML",
    "AI-TODO",
    "AI-PYTEST-SKIP",
    "AI-JEST-ONLY",
    "AI-CI-DISABLE",
    "UPD-HTTP-UPDATE-URL",
    "UPD-NO-SHA256",
    "UPD-NO-SIGNATURE",
    "UPD-AUTO-EXECUTE",
    "UPD-NO-ROLLBACK",
    "CHAT-UI-SCRAPING",
    "CHAT-TOKEN-LOGGING",
    "CHAT-SEND-FULL-CODE",
    "GIT-TEST-DELETION",
    "GIT-CI-CHANGE",
    "DEP-PACKAGE-NO-LOCK",
    "DOC-MISSING-README",
}


def _rules_payload() -> dict[str, object]:
    return json.loads(Path("src/codex_quality_gate/data/default_rules.json").read_text())


def _config_payload() -> dict[str, object]:
    return json.loads(Path("src/codex_quality_gate/data/default_config.json").read_text())


def test_default_rules_catalog_is_real_and_complete() -> None:
    payload = _rules_payload()
    rules = payload["rules"]
    assert payload["schema_version"] == 1
    assert payload["minimum_app_version"]
    assert len(rules) >= 100
    ids = {rule["id"] for rule in rules}
    assert REQUIRED_RULE_IDS.issubset(ids)
    for rule in rules:
        assert rule["repair_hint"]
        assert rule["fix_strategy"] in {"autofix", "manual", "review_required", "blocked"}
        assert rule["severity"] in {"critical", "error", "warning", "info"}
        re.compile(rule["regex"])


def test_default_config_matches_package_release_constants() -> None:
    payload = _config_payload()
    app_payload = payload["app"]
    updates_payload = payload["updates"]

    assert app_payload["version"] == VERSION
    assert updates_payload["ed25519_public_key_base64"] == DEFAULT_ED25519_PUBLIC_KEY_BASE64


def test_default_semgrep_catalog_is_not_empty() -> None:
    payload = yaml.safe_load(Path("src/codex_quality_gate/data/default_semgrep.yml").read_text())
    rules = payload["rules"]
    ids = {rule["id"] for rule in rules}
    assert len(rules) >= 20
    assert {
        "cqg.python.eval",
        "cqg.javascript.eval",
        "cqg.updater.no-signature",
        "cqg.chat.no-audit",
    }.issubset(ids)


def test_orchestrator_runs_plan_items_and_returns_check_results(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "x.py").write_text("value = 1\n", encoding="utf-8")
    result = CheckOrchestrator().run(tmp_path, profile_name="minimal")
    assert result.check_results
    assert {item.check_id for item in result.check_results}.issuperset(
        {"syntax_compile", "custom_rules", "docs_check"}
    )


def test_update_security_rejects_redirect_size_replay_downgrade_and_traversal(
    tmp_path: Path,
) -> None:
    from codex_quality_gate.updates.security import (
        reject_downgrade,
        reject_expired_manifest,
        reject_replay_manifest,
        reject_symlink_target,
        safe_join,
        validate_file_size,
        validate_no_redirect_to_untrusted_domain,
    )

    with pytest.raises(SecurityVerificationError):
        validate_no_redirect_to_untrusted_domain(
            "https://good.example/latest.json",
            "https://evil.example/latest.json",
            ["good.example"],
        )
    with pytest.raises(SecurityVerificationError):
        validate_file_size(101, 100)
    with pytest.raises(SecurityVerificationError):
        reject_replay_manifest({"manifest_id": "m1"}, ["m1"])
    with pytest.raises(SecurityVerificationError):
        reject_downgrade("1.0.0", "2.0.0")
    with pytest.raises(SecurityVerificationError):
        reject_expired_manifest({"expires_at": "2000-01-01T00:00:00Z"})
    with pytest.raises(SecurityVerificationError):
        safe_join(tmp_path, "../outside.json")
    from codex_quality_gate.updates.cache import cache_payload

    with pytest.raises(SecurityVerificationError):
        cache_payload(tmp_path, "../outside.json", b"{}")
    symlink = tmp_path / "rules.json"
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    try:
        symlink.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this platform")
    with pytest.raises(SecurityVerificationError):
        reject_symlink_target(symlink)


def test_policy_blocks_deleted_tests_and_disabled_ci() -> None:
    from codex_quality_gate.policies.risk_policy import RiskPolicy

    assert AutofixPolicy().requires_review("tests/test_x.py", change_type="deleted")
    with pytest.raises(PolicyViolationError):
        RiskPolicy().validate_diff(
            "diff --git a/tests/test_x.py b/tests/test_x.py\n--- a/tests/test_x.py\n+++ /dev/null"
        )
    with pytest.raises(PolicyViolationError):
        RiskPolicy().validate_diff("+ ci: false")


def test_cli_invalid_profile_returns_exit_2_without_traceback() -> None:
    result = CliRunner().invoke(app, ["bootstrap", ".", "--profile", "does-not-exist"])
    assert result.exit_code == 2
    assert "Traceback" not in result.output


@pytest.mark.parametrize(
    ("text", "action", "target"),
    [
        ("Проверь проект backend-api", "scan_project", "backend-api"),
        ("Установи проверки для backend-api", "bootstrap_project", "backend-api"),
        ("Обнови правила для frontend", "update_rules", "frontend"),
        ("Покажи ошибки backend-api", "show_findings", "backend-api"),
        ("Отправь отчёт backend-api", "send_report", "backend-api"),
        ("Объясни ошибку SEC-PY-EVAL", "explain_finding", "SEC-PY-EVAL"),
        ("Разрешаю safe autofix для run 123", "approve_autofix", "123"),
        ("approve safe autofix run 123", "approve_autofix", "123"),
    ],
)
def test_chat_router_parses_required_commands(text: str, action: str, target: str) -> None:
    command = parse_chat_command(text)
    assert command is not None
    assert command.action == action
    assert command.project == target
