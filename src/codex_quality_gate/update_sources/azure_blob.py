from __future__ import annotations

from typing import Any


class AzureBlobSource:
    def __init__(self, **config: Any) -> None:
        self.config = config

    def latest(self) -> dict[str, Any]:
        return {"source": "azure_blob", "enabled": bool(self.config.get("enabled", True))}
