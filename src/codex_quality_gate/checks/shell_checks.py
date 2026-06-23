from __future__ import annotations

from codex_quality_gate.checks.simple import ProfileMarkerCheck, default_module_check

CHECK_NAME = "shell"


def create_checks() -> list[ProfileMarkerCheck]:
    return [
        default_module_check(
            CHECK_NAME,
        )
    ]
