from __future__ import annotations

from pathlib import Path

from codex_quality_gate.checks.ai_codex_checks import create_checks
from codex_quality_gate.checks.base import CheckContext, CheckStatus
from codex_quality_gate.core.result import ProjectProfile


def test_ai_codex_module_exposes_runnable_check(tmp_path: Path) -> None:
    check = create_checks()[0]
    result = check.run(CheckContext(root=tmp_path, profile=ProjectProfile(tmp_path)))
    assert result.check_id == "ai_codex"
    assert result.status is CheckStatus.PASSED
