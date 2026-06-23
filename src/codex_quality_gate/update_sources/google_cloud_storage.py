from __future__ import annotations

from typing import Any


class GoogleCloudStorageSource:
    def __init__(self, **config: Any) -> None:
        self.config = config

    def latest(self) -> dict[str, Any]:
        return {"source": "google_cloud_storage", "enabled": bool(self.config.get("enabled", True))}
