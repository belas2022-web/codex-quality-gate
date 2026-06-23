from __future__ import annotations

import pytest

from codex_quality_gate.core.errors import PolicyViolationError
from codex_quality_gate.policies.autofix_policy import AutofixPolicy
from codex_quality_gate.policies.chat_policy import validate_full_code_send, validate_writeback
from codex_quality_gate.policies.risk_policy import block_ci_disable, block_security_disable


def test_autofix_observe_does_not_modify() -> None:
    assert AutofixPolicy().requires_review(".github/workflows/quality.yml")


def test_autofix_safe_only_allowed_tools() -> None:
    AutofixPolicy().validate_tool("ruff-format")
    with pytest.raises(PolicyViolationError):
        AutofixPolicy().validate_tool("unsafe")


def test_policy_blocks_ci_modification() -> None:
    with pytest.raises(PolicyViolationError):
        block_ci_disable("+ ci: false")


def test_policy_blocks_test_deletion() -> None:
    assert AutofixPolicy().requires_review("tests/test_x.py") is False


def test_policy_blocks_security_disable() -> None:
    with pytest.raises(PolicyViolationError):
        block_security_disable("+ security: false")


def test_policy_requires_review_for_auth() -> None:
    assert AutofixPolicy().requires_review("auth/login.py")


def test_policy_requires_review_for_updater() -> None:
    assert AutofixPolicy().requires_review("updater/client.py")


def test_writeback_permission_policy() -> None:
    with pytest.raises(PolicyViolationError):
        validate_writeback(False)


def test_full_code_policy() -> None:
    with pytest.raises(PolicyViolationError):
        validate_full_code_send(False)
