from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

DEFAULT_IGNORES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "tests",
    "htmlcov",
}


def is_ignored(path: Path, root: Path, ignored_names: set[str] | None = None) -> bool:
    ignored = ignored_names or DEFAULT_IGNORES
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    return any(part in ignored for part in relative.parts)


def iter_project_files(
    root: str | Path,
    suffixes: set[str] | None = None,
    ignored_names: set[str] | None = None,
) -> Iterator[Path]:
    base = Path(root).resolve()
    ignored = ignored_names or DEFAULT_IGNORES
    normalized_suffixes = {suffix.lower() for suffix in suffixes} if suffixes else None
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [dirname for dirname in dirnames if dirname not in ignored]
        directory = Path(dirpath)
        if is_ignored(directory, base, ignored):
            continue
        for filename in filenames:
            path = directory / filename
            if is_ignored(path, base, ignored):
                continue
            if normalized_suffixes and path.suffix.lower() not in normalized_suffixes:
                continue
            yield path
