from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class UpdateManifest:
    version: str
    created_at: str
    expires_at: str
    rules_url: str
    rules_sha256: str
    rules_signature: str
    manifest_signature: str = ""
    app_artifact_url: str = ""
    app_artifact_sha256: str = ""
    app_artifact_signature: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> UpdateManifest:
        return cls(
            version=str(payload.get("version", "")),
            created_at=str(payload.get("created_at", "")),
            expires_at=str(payload.get("expires_at", "")),
            rules_url=str(payload.get("rules_url", "")),
            rules_sha256=str(payload.get("rules_sha256", "")),
            rules_signature=str(payload.get("rules_signature", "")),
            manifest_signature=str(payload.get("manifest_signature", "")),
            app_artifact_url=str(payload.get("app_artifact_url", "")),
            app_artifact_sha256=str(payload.get("app_artifact_sha256", "")),
            app_artifact_signature=str(payload.get("app_artifact_signature", "")),
        )

    def canonical_bytes(self) -> bytes:
        parts = [
            self.version,
            self.created_at,
            self.expires_at,
            self.rules_url,
            self.rules_sha256,
            self.app_artifact_url,
            self.app_artifact_sha256,
        ]
        return "\n".join(parts).encode("utf-8")
