from __future__ import annotations

from pathlib import Path

from codex_quality_gate.core.result import Finding, Severity
from codex_quality_gate.database.repository import Repository
from codex_quality_gate.database.sqlite import connect


def test_scan_run_saved(tmp_path: Path) -> None:
    repo = Repository(connect(tmp_path / "db.sqlite"))
    assert repo.create_scan_run("demo") == 1


def test_findings_saved(tmp_path: Path) -> None:
    repo = Repository(connect(tmp_path / "db.sqlite"))
    run_id = repo.create_scan_run("demo")
    repo.save_finding(run_id, Finding("1", "x.py", 1, 1, Severity.ERROR, "bad", "rule", "cat"))
    assert repo.list_findings()[0]["rule_id"] == "rule"


def test_update_history_saved(tmp_path: Path) -> None:
    repo = Repository(connect(tmp_path / "db.sqlite"))
    repo.save_update_history("1", "ok")
    assert repo.list_update_history()[0]["status"] == "ok"


def test_audit_event_saved(tmp_path: Path) -> None:
    repo = Repository(connect(tmp_path / "db.sqlite"))
    repo.save_audit_event("x", {"ok": True})
    assert repo.list_audit_events()[0]["payload"] == {"ok": True}


def test_policy_violation_saved(tmp_path: Path) -> None:
    repo = Repository(connect(tmp_path / "db.sqlite"))
    repo.save_policy_violation("p", "r")
    row = repo.connection.execute("SELECT policy, reason FROM policy_violations").fetchone()
    assert row == ("p", "r")
