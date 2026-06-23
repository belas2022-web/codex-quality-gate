from __future__ import annotations

from codex_quality_gate.core.errors import SecurityVerificationError
from codex_quality_gate.updates.models import UpdateManifest
from codex_quality_gate.updates.signatures import verify_ed25519


def verify_manifest(manifest: UpdateManifest, public_key_base64: str) -> None:
    if not manifest.manifest_signature:
        raise SecurityVerificationError("Manifest signature is required")
    if not verify_ed25519(
        manifest.canonical_bytes(), manifest.manifest_signature, public_key_base64
    ):
        raise SecurityVerificationError("Manifest signature mismatch")
