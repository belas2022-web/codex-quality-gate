from __future__ import annotations

import json
from pathlib import Path

from codex_quality_gate.projects.project_config import ProjectConfig


class ProjectRegistry:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _load(self) -> dict[str, dict[str, str]]:
        if not self.path.exists():
            return {}
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}

    def _save(self, payload: dict[str, dict[str, str]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def add(self, name: str, path: str | Path, mode: str = "observe") -> ProjectConfig:
        if "/" in name or "\\" in name or name in {"", ".", ".."}:
            raise ValueError("Project name must be a simple identifier")
        root = Path(path).resolve()
        if not root.exists():
            raise FileNotFoundError(f"Project path does not exist: {root}")
        payload = self._load()
        payload[name] = {"name": name, "path": str(root), "mode": mode}
        self._save(payload)
        return ProjectConfig(name=name, path=root, mode=mode)

    def list(self) -> list[ProjectConfig]:
        return [
            ProjectConfig(
                name=item["name"], path=Path(item["path"]), mode=item.get("mode", "observe")
            )
            for item in self._load().values()
        ]

    def get(self, name: str) -> ProjectConfig:
        payload = self._load()
        if name not in payload:
            raise KeyError(name)
        item = payload[name]
        return ProjectConfig(
            name=item["name"], path=Path(item["path"]), mode=item.get("mode", "observe")
        )

    def remove(self, name: str) -> None:
        payload = self._load()
        payload.pop(name, None)
        self._save(payload)
