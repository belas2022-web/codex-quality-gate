from __future__ import annotations

from typing import Any


class DockerRegistrySource:
    def __init__(self, **config: Any) -> None:
        self.config = config

    def latest(self) -> dict[str, Any]:
        return {"source": "docker_registry", "enabled": bool(self.config.get("enabled", True))}
