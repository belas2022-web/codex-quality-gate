from __future__ import annotations

from pathlib import Path

from codex_quality_gate.core.errors import SecurityVerificationError
from codex_quality_gate.updates.filesystem import UpdateLock, atomic_write, backup_file
from codex_quality_gate.updates.hashing import sha256_bytes
from codex_quality_gate.updates.models import UpdateManifest
from codex_quality_gate.updates.security import (
    reject_symlink_target,
    safe_join,
    validate_update_url,
)
from codex_quality_gate.updates.signatures import verify_ed25519
from codex_quality_gate.updates.update_client import DEFAULT_MAX_UPDATE_BYTES, UpdateClient


class Updater:
    def __init__(
        self,
        allowed_domains: list[str],
        public_key_base64: str,
        client: UpdateClient | None = None,
        data_dir: str | Path | None = None,
        max_update_bytes: int = DEFAULT_MAX_UPDATE_BYTES,
    ) -> None:
        self.allowed_domains = allowed_domains
        self.public_key_base64 = public_key_base64
        self.client = client or UpdateClient()
        base_dir = Path(data_dir or ".codex-quality-gate")
        self.rules_base_dir = base_dir / "rules"
        self.downloads_base_dir = base_dir / "downloads"
        self.locks_base_dir = base_dir / "locks"
        self.max_update_bytes = max_update_bytes

    def verify_rules_payload(self, manifest: UpdateManifest, payload: bytes) -> None:
        if sha256_bytes(payload) != manifest.rules_sha256:
            raise SecurityVerificationError("Rules hash mismatch")
        if not verify_ed25519(payload, manifest.rules_signature, self.public_key_base64):
            raise SecurityVerificationError("Rules signature mismatch")

    def download_rules(self, manifest: UpdateManifest) -> bytes:
        validate_update_url(manifest.rules_url, self.allowed_domains)
        payload = self.client.get_bytes(
            manifest.rules_url,
            allowed_domains=self.allowed_domains,
            max_size_bytes=self.max_update_bytes,
        )
        self.verify_rules_payload(manifest, payload)
        return payload

    def apply_rules(
        self, manifest: UpdateManifest, target_path: str | Path, lock_path: str | Path
    ) -> None:
        target = self._rules_path(target_path)
        lock = self._lock_path(lock_path)
        with UpdateLock(lock):
            backup = backup_file(target)
            payload = self.download_rules(manifest)
            try:
                atomic_write(target, payload)
            except OSError:
                if backup.exists():
                    atomic_write(target, backup.read_bytes())
                raise

    def download_app_artifact(self, manifest: UpdateManifest) -> bytes:
        if not manifest.app_artifact_url:
            raise SecurityVerificationError("Manifest has no app artifact URL")
        validate_update_url(manifest.app_artifact_url, self.allowed_domains)
        payload = self.client.get_bytes(
            manifest.app_artifact_url,
            allowed_domains=self.allowed_domains,
            max_size_bytes=self.max_update_bytes,
        )
        if sha256_bytes(payload) != manifest.app_artifact_sha256:
            raise SecurityVerificationError("App artifact hash mismatch")
        if not verify_ed25519(payload, manifest.app_artifact_signature, self.public_key_base64):
            raise SecurityVerificationError("App artifact signature mismatch")
        return payload

    def _rules_path(self, target_path: str | Path) -> Path:
        target = safe_join(self.rules_base_dir, target_path)
        reject_symlink_target(target)
        return target

    def _lock_path(self, lock_path: str | Path) -> Path:
        lock = safe_join(self.locks_base_dir, lock_path)
        reject_symlink_target(lock)
        return lock
