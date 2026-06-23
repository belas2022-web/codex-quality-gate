from __future__ import annotations

import json
from pathlib import Path

from codex_quality_gate.scanner.ignore import iter_project_files


def _read_package_json(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def detect_frameworks(root: Path) -> list[str]:
    frameworks: set[str] = set()
    names = {path.name for path in iter_project_files(root)}
    for package_json in iter_project_files(root, {".json"}):
        if package_json.name != "package.json":
            continue
        payload = _read_package_json(package_json)
        deps: dict[str, object] = {}
        for key in ("dependencies", "devDependencies"):
            value = payload.get(key)
            if isinstance(value, dict):
                deps.update(value)
        if "react" in deps:
            frameworks.add("react")
        if "vite" in deps or "vite.config.ts" in names:
            frameworks.add("vite")
        if "next" in deps or "next.config.js" in names:
            frameworks.add("next")
        if "express" in deps:
            frameworks.add("express")
    pyproject = (
        (root / "pyproject.toml").read_text(encoding="utf-8")
        if (root / "pyproject.toml").exists()
        else ""
    )
    requirements = (
        (root / "requirements.txt").read_text(encoding="utf-8")
        if (root / "requirements.txt").exists()
        else ""
    )
    python_deps = f"{pyproject}\n{requirements}".lower()
    if "fastapi" in python_deps:
        frameworks.add("fastapi")
    if "django" in python_deps:
        frameworks.add("django")
    if "flask" in python_deps:
        frameworks.add("flask")
    return sorted(frameworks)
