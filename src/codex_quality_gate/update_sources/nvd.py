from __future__ import annotations

from typing import Any


class NvdSource:
    def __init__(self, **config: Any) -> None:
        self.config = config

    def latest(self) -> dict[str, Any]:
        return {"source": "nvd", "enabled": bool(self.config.get("enabled", True))}
