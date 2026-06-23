from __future__ import annotations

from codex_quality_gate.policies.autofix_policy import AutofixPolicy
from codex_quality_gate.scanner.diff_scanner import parse_simple_diff


def test_test_deletion_blocked() -> None:
    assert parse_simple_diff("+++ b/tests/test_x.py\n-old")


def test_ci_change_requires_review() -> None:
    assert AutofixPolicy().requires_review(".github/workflows/quality.yml")


def test_security_file_change_requires_review() -> None:
    assert AutofixPolicy().requires_review("security/policy.py")


def test_updater_change_requires_review() -> None:
    assert AutofixPolicy().requires_review("updater/client.py")


def test_env_file_committed_blocked() -> None:
    assert ".env".startswith(".env")
