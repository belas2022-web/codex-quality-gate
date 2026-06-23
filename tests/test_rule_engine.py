from __future__ import annotations

import pytest

from codex_quality_gate.core.result import Severity
from codex_quality_gate.rules.models import Rule
from codex_quality_gate.rules.rule_engine import RuleEngine
from codex_quality_gate.rules.validator import validate_rules


def _first_rule_id(text: str) -> str:
    findings = RuleEngine().scan_text("x.py", text)
    assert findings
    return findings[0].rule_id


def test_detects_eval() -> None:
    assert _first_rule_id("value = eval(user_input)") == "SEC-PY-EVAL"


def test_detects_exec() -> None:
    assert _first_rule_id("exec(user_input)") == "SEC-PY-EXEC"


def test_detects_shell_true() -> None:
    assert _first_rule_id("subprocess.run(['x'], shell=True)") == "SEC-PY-SHELL-TRUE"


def test_detects_pickle() -> None:
    assert _first_rule_id("pickle.loads(data)") == "SEC-PY-PICKLE-LOADS"


def test_detects_yaml_load() -> None:
    assert _first_rule_id("yaml.load(data)") == "SEC-PY-YAML-LOAD"


def test_detects_verify_false() -> None:
    assert _first_rule_id("requests.get(url, verify=False, timeout=3)") == "SEC-PY-VERIFY-FALSE"


def test_detects_no_timeout() -> None:
    assert _first_rule_id("requests.get(url)") == "SEC-PY-REQUESTS-NO-TIMEOUT"


def test_detects_hardcoded_secret() -> None:
    assert _first_rule_id("api_key = '1234567890123456'") == "SEC-PY-HARDCODED-SECRET"


def test_detects_todo() -> None:
    assert _first_rule_id("# TO" + "DO: fix") == "AI-TODO"


def test_detects_pytest_skip() -> None:
    assert _first_rule_id("pytest.skip('x')") == "AI-PYTEST-SKIP"


def test_rejects_duplicate_rule_ids() -> None:
    rule = Rule("x", "x", "x", Severity.WARNING, "x")
    with pytest.raises(ValueError):
        validate_rules([rule, rule])


def test_rejects_bad_regex() -> None:
    with pytest.raises(ValueError):
        validate_rules([Rule("x", "[", "x", Severity.WARNING, "x")])


def test_rejects_missing_required_fields() -> None:
    with pytest.raises(ValueError):
        validate_rules([Rule("", "x", "x", Severity.WARNING, "x")])
