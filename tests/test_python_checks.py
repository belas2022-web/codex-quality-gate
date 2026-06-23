from __future__ import annotations

from pathlib import Path

from codex_quality_gate.checks.base import CheckContext, CheckStatus
from codex_quality_gate.checks.orchestrator import CheckOrchestrator
from codex_quality_gate.checks.python_checks import create_checks
from codex_quality_gate.core.result import ProjectProfile


def test_python_module_runs_when_language_detected(tmp_path: Path) -> None:
    profile = ProjectProfile(tmp_path, languages=["python"])
    result = create_checks()[0].run(CheckContext(root=tmp_path, profile=profile))
    assert result.status is CheckStatus.PASSED


def test_python_syntax_compile_reports_error(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text("x =\n", encoding="utf-8")
    result = CheckOrchestrator().run(tmp_path, profile_name="minimal")
    assert any(finding.rule_id == "syntax_compile" for finding in result.findings)
