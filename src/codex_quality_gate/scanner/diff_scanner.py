from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DiffChange:
    path: str
    status: str
    added: list[str]
    removed: list[str]


def parse_simple_diff(text: str) -> list[DiffChange]:
    changes: list[DiffChange] = []
    current_path = ""
    added: list[str] = []
    removed: list[str] = []
    for line in text.splitlines():
        if line.startswith("+++ b/"):
            if current_path:
                changes.append(DiffChange(current_path, "modified", added, removed))
                added = []
                removed = []
            current_path = line.removeprefix("+++ b/")
        elif line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            removed.append(line[1:])
    if current_path:
        changes.append(DiffChange(current_path, "modified", added, removed))
    return changes
