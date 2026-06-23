from __future__ import annotations

import subprocess
from pathlib import Path

from codex_quality_gate.detection.project_profiler import ProjectProfiler
from codex_quality_gate.installers.install_plan import InstallPlan, InstallProfile
from codex_quality_gate.installers.tool_catalog import ToolCatalog


class Bootstrapper:
    def __init__(
        self, profiler: ProjectProfiler | None = None, catalog: ToolCatalog | None = None
    ) -> None:
        self.profiler = profiler or ProjectProfiler()
        self.catalog = catalog or ToolCatalog()

    def plan(
        self,
        path: str | Path,
        profile: InstallProfile = InstallProfile.STANDARD,
        apply: bool = False,
    ) -> InstallPlan:
        project_profile = self.profiler.profile(path)
        return self.catalog.create_plan(project_profile, profile=profile, dry_run=not apply)

    def execute(self, plan: InstallPlan) -> list[str]:
        if plan.dry_run:
            return [f"dry-run: {' '.join(item.install_command)}" for item in plan.requirements]
        results: list[str] = []
        for item in plan.requirements:
            if item.global_install or item.requires_admin:
                raise PermissionError(f"Unsafe install requirement blocked: {item.name}")
            completed = subprocess.run(
                item.install_command,
                check=False,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    f"Install command failed for {item.name}: {completed.stderr.strip()}"
                )
            results.append(f"installed: {item.name}")
        return results
