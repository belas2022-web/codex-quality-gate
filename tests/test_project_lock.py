from __future__ import annotations

from pathlib import Path

import pytest

from codex_quality_gate.projects.project_lock import ProjectLock
from codex_quality_gate.projects.scheduler import run_each_project


def test_project_lock_prevents_double_scan(tmp_path: Path) -> None:
    lock = ProjectLock(tmp_path / "demo.lock")
    lock.acquire()
    with pytest.raises(RuntimeError):
        ProjectLock(tmp_path / "demo.lock").acquire()
    lock.release()


def test_multiple_projects_scan_independently() -> None:
    assert run_each_project(["a", "b"], lambda name: name == "a") == {"a": True, "b": False}


def test_one_project_failure_does_not_stop_all() -> None:
    def scan(name: str) -> bool:
        if name == "bad":
            raise RuntimeError("bad")
        return True

    assert run_each_project(["good", "bad", "next"], scan) == {
        "good": True,
        "bad": False,
        "next": True,
    }
