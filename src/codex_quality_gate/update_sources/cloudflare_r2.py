from __future__ import annotations

from typing import Any


class CloudflareR2Source:
    def __init__(self, **config: Any) -> None:
        self.config = config

    def latest(self) -> dict[str, Any]:
        return {"source": "cloudflare_r2", "enabled": bool(self.config.get("enabled", True))}
