from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from pytest import MonkeyPatch
from typer.testing import CliRunner

from codex_quality_gate.cli import app

runner = CliRunner()


def test_cli_check_returns_1_on_error(tmp_path: Path) -> None:
    (tmp_path / "bad.py").write_text("eval(x)", encoding="utf-8")
    result = runner.invoke(app, ["check", str(tmp_path)])
    assert result.exit_code == 1


def test_python_module_check_returns_process_exit_code(tmp_path: Path) -> None:
    (tmp_path / "bad.py").write_text("eval(x)", encoding="utf-8")
    env = os.environ.copy()
    src_path = str(Path.cwd() / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        [sys.executable, "-m", "codex_quality_gate", "check", str(tmp_path), "--json"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert completed.returncode == 1
    assert json.loads(completed.stdout)["summary"]["errors"] >= 1


def test_cli_check_returns_0_on_warning(tmp_path: Path) -> None:
    (tmp_path / "warn.py").write_text("requests.get(url)", encoding="utf-8")
    result = runner.invoke(app, ["check", str(tmp_path)])
    assert result.exit_code == 0


def test_cli_check_fail_on_warning_returns_1(tmp_path: Path) -> None:
    (tmp_path / "warn.py").write_text("requests.get(url)", encoding="utf-8")
    result = runner.invoke(app, ["check", str(tmp_path), "--fail-on-warning"])
    assert result.exit_code == 1


def test_cli_profile_outputs_json(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'", encoding="utf-8")
    result = runner.invoke(app, ["profile", str(tmp_path), "--json"])
    assert result.exit_code == 0
    assert "languages" in result.output


def test_cli_bootstrap_dry_run(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'", encoding="utf-8")
    result = runner.invoke(app, ["bootstrap", str(tmp_path), "--dry-run"])
    assert result.exit_code == 0
    assert "dry_run" in result.output


def test_cli_sources_list() -> None:
    result = runner.invoke(app, ["sources", "list"])
    assert result.exit_code == 0
    assert "github_pages" in result.output


def test_cli_chat_list() -> None:
    result = runner.invoke(app, ["chat", "list"])
    assert result.exit_code == 0
    assert "slack" in result.output


def test_cli_audit_tail() -> None:
    result = runner.invoke(app, ["audit", "tail"])
    assert result.exit_code == 0


def test_cli_update_commands_validate_catalogs() -> None:
    for args in (["check-catalogs"], ["update-rules"], ["check-update"], ["download-update"]):
        result = runner.invoke(app, args)
        assert result.exit_code == 0
        assert json.loads(result.output)["rules"] == 100


def test_cli_dashboard_sources_chat_and_audit_commands() -> None:
    help_result = runner.invoke(app, ["--help"])
    assert help_result.exit_code == 0
    assert "dashboard " not in help_result.output
    assert runner.invoke(app, ["dashboard-api", "--check-config"]).exit_code == 0
    assert runner.invoke(app, ["sources", "sync"]).exit_code == 0
    assert runner.invoke(app, ["chat", "test", "slack"]).exit_code == 0
    send_report = runner.invoke(app, ["chat", "send-report", "demo", "--connector", "slack"])
    assert send_report.exit_code == 0
    assert runner.invoke(app, ["audit", "export", "--json"]).output.strip() == "[]"
    assert "<html>" in runner.invoke(app, ["audit", "export", "--html"]).output


def test_cli_project_lifecycle_commands(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "bad.py").write_text("eval(x)\n", encoding="utf-8")

    assert runner.invoke(app, ["project", "add", "demo", str(project_dir)]).exit_code == 0
    listed = json.loads(runner.invoke(app, ["project", "list"]).output)
    assert listed[0]["name"] == "demo"
    assert runner.invoke(app, ["project", "profile", "demo"]).exit_code == 0
    assert runner.invoke(app, ["project", "bootstrap", "demo"]).exit_code == 0
    scan = runner.invoke(app, ["project", "scan", "demo"])
    assert scan.exit_code == 1
    assert "SEC-PY-EVAL" in scan.output
    assert runner.invoke(app, ["project", "update-rules", "demo"]).exit_code == 0
    assert runner.invoke(app, ["project", "remove", "demo"]).exit_code == 0
