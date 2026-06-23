from __future__ import annotations

from pathlib import Path

from codex_quality_gate.scanner.ignore import iter_project_files

LANGUAGE_INDICATORS: dict[str, tuple[str, ...]] = {
    "python": (
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
        "pytest.ini",
        "ruff.toml",
        ".ruff.toml",
    ),
    "javascript": ("package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"),
    "typescript": ("tsconfig.json", "vite.config.ts", "next.config.js"),
    "go": ("go.mod", "go.sum"),
    "rust": ("Cargo.toml", "Cargo.lock"),
    "java": ("pom.xml", "build.gradle", "build.gradle.kts"),
    "dotnet": (".sln", ".csproj"),
}


def detect_languages(root: Path) -> list[str]:
    found: set[str] = set()
    names = {path.name for path in iter_project_files(root)}
    for language, indicators in LANGUAGE_INDICATORS.items():
        for indicator in indicators:
            suffix_match = indicator.startswith(".") and any(
                name.endswith(indicator) for name in names
            )
            if suffix_match or indicator in names:
                found.add(language)
    return sorted(found)
