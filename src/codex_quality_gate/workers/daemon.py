from __future__ import annotations

from codex_quality_gate.core.result import AutonomyMode
from codex_quality_gate.projects.registry import ProjectRegistry
from codex_quality_gate.projects.scheduler import run_each_project


class Daemon:
    def __init__(
        self, registry: ProjectRegistry, mode: AutonomyMode = AutonomyMode.OBSERVE
    ) -> None:
        self.registry = registry
        self.mode = mode

    def run_once(self) -> dict[str, bool]:
        projects = [project.name for project in self.registry.list()]
        return run_each_project(projects, lambda _name: True)
