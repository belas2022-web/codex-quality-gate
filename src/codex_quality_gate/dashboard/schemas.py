from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DashboardConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    auth_token: str | None = None
    database_path: Path | None = None
    config_path: Path | None = None
