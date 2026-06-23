from __future__ import annotations

from typing import Any


class OsvSource:
    def __init__(self, **config: Any) -> None:
        self.config = config

    def latest(self) -> dict[str, Any]:
        return {"source": "osv", "enabled": bool(self.config.get("enabled", True))}
