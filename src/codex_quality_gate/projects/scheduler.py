from __future__ import annotations

from collections.abc import Callable


def run_each_project(project_names: list[str], scan: Callable[[str], bool]) -> dict[str, bool]:
    results: dict[str, bool] = {}
    for name in project_names:
        try:
            results[name] = scan(name)
        except Exception:
            results[name] = False
    return results
