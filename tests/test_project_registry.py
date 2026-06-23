from __future__ import annotations

from pathlib import Path

import pytest

from codex_quality_gate.projects.registry import ProjectRegistry


def test_add_project_success(tmp_path: Path) -> None:
    registry = ProjectRegistry(tmp_path / "projects.json")
    project = registry.add("demo", tmp_path)
    assert project.name == "demo"


def test_reject_missing_project_path(tmp_path: Path) -> None:
    registry = ProjectRegistry(tmp_path / "projects.json")
    with pytest.raises(FileNotFoundError):
        registry.add("demo", tmp_path / "missing")


def test_reject_path_traversal(tmp_path: Path) -> None:
    registry = ProjectRegistry(tmp_path / "projects.json")
    with pytest.raises(ValueError):
        registry.add("../demo", tmp_path)


def test_per_project_policy_applied(tmp_path: Path) -> None:
    registry = ProjectRegistry(tmp_path / "projects.json")
    registry.add("demo", tmp_path, mode="observe")
    assert registry.get("demo").mode == "observe"
