from __future__ import annotations

from pathlib import Path

from codex_quality_gate.scanner.ignore import iter_project_files


def detect_package_managers(root: Path) -> list[str]:
    markers = {
        "pip": ["requirements.txt", "pyproject.toml"],
        "poetry": ["poetry.lock"],
        "pdm": ["pdm.lock"],
        "uv": ["uv.lock"],
        "npm": ["package-lock.json", "package.json"],
        "pnpm": ["pnpm-lock.yaml"],
        "yarn": ["yarn.lock"],
        "go": ["go.mod"],
        "cargo": ["Cargo.toml"],
        "maven": ["pom.xml"],
        "gradle": ["build.gradle", "build.gradle.kts"],
        "dotnet": [".sln", ".csproj"],
    }
    names = {path.name for path in iter_project_files(root)}
    result: set[str] = set()
    for manager, indicators in markers.items():
        for indicator in indicators:
            suffix_match = indicator.startswith(".") and any(
                name.endswith(indicator) for name in names
            )
            if suffix_match or indicator in names:
                result.add(manager)
    return sorted(result)
