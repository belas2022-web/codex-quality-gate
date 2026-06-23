from __future__ import annotations

from codex_quality_gate.installers.install_plan import ToolRequirement


class DotnetInstaller:
    def plan(self) -> list[ToolRequirement]:
        return []
