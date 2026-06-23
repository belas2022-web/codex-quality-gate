from __future__ import annotations

from pathlib import Path

from codex_quality_gate.checks.base import CheckContext, CheckStatus
from codex_quality_gate.checks.javascript_checks import create_checks as create_js_checks
from codex_quality_gate.checks.typescript_checks import create_checks as create_ts_checks
from codex_quality_gate.core.result import ProjectProfile
from codex_quality_gate.rules.rule_engine import RuleEngine


def test_javascript_module_runs_when_language_detected(tmp_path: Path) -> None:
    profile = ProjectProfile(tmp_path, languages=["javascript"])
    result = create_js_checks()[0].run(CheckContext(root=tmp_path, profile=profile))
    assert result.status is CheckStatus.PASSED


def test_typescript_module_runs_when_language_detected(tmp_path: Path) -> None:
    profile = ProjectProfile(tmp_path, languages=["typescript"])
    result = create_ts_checks()[0].run(CheckContext(root=tmp_path, profile=profile))
    assert result.status is CheckStatus.PASSED


def test_jest_only_is_detected() -> None:
    findings = RuleEngine().scan_text("x.test.ts", "test.only('x', () => {})")
    assert findings[0].rule_id == "AI-JEST-ONLY"
