from __future__ import annotations

from codex_quality_gate.checks.simple import ProfileMarkerCheck, default_module_check

CHECK_NAME = "dependency"


def create_checks() -> list[ProfileMarkerCheck]:
    return [
        default_module_check(
            CHECK_NAME,
            package_managers=(
                "pip",
                "poetry",
                "pdm",
                "uv",
                "npm",
                "pnpm",
                "yarn",
                "go",
                "cargo",
                "maven",
                "gradle",
                "dotnet",
            ),
        )
    ]
