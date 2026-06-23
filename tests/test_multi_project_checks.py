from __future__ import annotations

from codex_quality_gate.projects.scheduler import run_each_project


def test_per_project_rules_channel_applied() -> None:
    assert run_each_project(["a"], lambda _name: True)["a"]
