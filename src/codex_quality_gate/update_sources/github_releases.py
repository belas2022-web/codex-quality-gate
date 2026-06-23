from __future__ import annotations

from typing import Any

from codex_quality_gate.updates.update_client import UpdateClient


class GitHubReleasesSource:
    def __init__(self, repository: str, client: UpdateClient | None = None) -> None:
        self.repository = repository
        self.client = client or UpdateClient()

    def latest(self) -> dict[str, Any]:
        owner, repo = self.repository.split("/", maxsplit=1)
        return self.client.get_json(f"https://api.github.com/repos/{owner}/{repo}/releases/latest")
