from __future__ import annotations

from typing import Any

from codex_quality_gate.updates.update_client import UpdateClient


class GitHubPagesSource:
    def __init__(self, manifest_url: str, client: UpdateClient | None = None) -> None:
        self.manifest_url = manifest_url
        self.client = client or UpdateClient()

    def latest(self) -> dict[str, Any]:
        return self.client.get_json(self.manifest_url)
