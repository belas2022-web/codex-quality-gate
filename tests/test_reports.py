from __future__ import annotations

import json
from pathlib import Path

from codex_quality_gate.checks.orchestrator import CheckOrchestrator
from codex_quality_gate.reporting.html import render_html
from codex_quality_gate.reporting.json_report import render_json
from codex_quality_gate.reporting.junit import render_junit
from codex_quality_gate.reporting.markdown import render_markdown
from codex_quality_gate.reporting.sarif import render_sarif


def _result(tmp_path: Path):
    (tmp_path / "x.py").write_text("eval(x)", encoding="utf-8")
    return CheckOrchestrator().run(tmp_path)


def test_json_report_valid(tmp_path: Path) -> None:
    assert json.loads(render_json(_result(tmp_path)))["findings"]


def test_sarif_report_valid(tmp_path: Path) -> None:
    assert json.loads(render_sarif(_result(tmp_path)))["version"] == "2.1.0"


def test_junit_report_valid(tmp_path: Path) -> None:
    assert "<testsuite" in render_junit(_result(tmp_path))


def test_html_report_created(tmp_path: Path) -> None:
    assert "<html" in render_html(_result(tmp_path))


def test_markdown_report_created(tmp_path: Path) -> None:
    assert "codex-quality-gate report" in render_markdown(_result(tmp_path))
