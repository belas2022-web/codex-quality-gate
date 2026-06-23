from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    path: Path
    mode: str = "observe"

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "path": str(self.path), "mode": self.mode}
