from __future__ import annotations

import base64
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from codex_quality_gate.core.errors import SecurityVerificationError
from codex_quality_gate.updates.filesystem import UpdateLock, atomic_write, backup_file
from codex_quality_gate.updates.hashing import sha256_bytes
from codex_quality_gate.updates.models import UpdateManifest
from codex_quality_gate.updates.signatures import verify_ed25519
from codex_quality_gate.updates.updater import Updater
from codex_quality_gate.updates.versioning import is_newer, reject_downgrade


def _keys() -> tuple[str, str]:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes_raw()
    signature = private.sign(b"rules")
    return base64.b64encode(public).decode(), base64.b64encode(signature).decode()


def test_manifest_signature_required() -> None:
    from codex_quality_gate.updates.manifest import verify_manifest

    public_key, _signature = _keys()
    manifest = UpdateManifest("1.0.0", "now", "later", "https://x/rules", "x", "x")
    with pytest.raises(SecurityVerificationError):
        verify_manifest(manifest, public_key)


def test_invalid_manifest_signature_rejected() -> None:
    assert not verify_ed25519(
        b"x", base64.b64encode(b"bad").decode(), base64.b64encode(b"0" * 32).decode()
    )


def test_rules_hash_mismatch_rejected() -> None:
    public_key, signature = _keys()
    manifest = UpdateManifest("1", "n", "l", "https://good/rules", "bad", signature)
    with pytest.raises(SecurityVerificationError):
        Updater(["good"], public_key).verify_rules_payload(manifest, b"rules")


def test_rules_signature_mismatch_rejected() -> None:
    public_key, _signature = _keys()
    manifest = UpdateManifest(
        "1",
        "n",
        "l",
        "https://good/rules",
        sha256_bytes(b"rules"),
        base64.b64encode(b"bad").decode(),
    )
    with pytest.raises(SecurityVerificationError):
        Updater(["good"], public_key).verify_rules_payload(manifest, b"rules")


def test_app_signature_mismatch_rejected() -> None:
    public_key, _signature = _keys()
    manifest = UpdateManifest(
        "1",
        "n",
        "l",
        "https://good/rules",
        "x",
        "x",
        app_artifact_url="https://good/app",
        app_artifact_sha256=sha256_bytes(b"app"),
        app_artifact_signature=base64.b64encode(b"bad").decode(),
    )

    class Client:
        def get_bytes(
            self,
            _url: str,
            *,
            allowed_domains: list[str],
            max_size_bytes: int,
        ) -> bytes:
            assert allowed_domains == ["good"]
            assert max_size_bytes > 0
            return b"app"

    with pytest.raises(SecurityVerificationError):
        Updater(["good"], public_key, Client()).download_app_artifact(manifest)  # type: ignore[arg-type]


def test_downgrade_rejected() -> None:
    with pytest.raises(ValueError):
        reject_downgrade("1.0.0", "2.0.0")


def test_version_1_10_is_newer_than_1_2() -> None:
    assert is_newer("1.10", "1.2")


def test_atomic_replace_success(tmp_path: Path) -> None:
    path = tmp_path / "rules.json"
    atomic_write(path, b"new")
    assert path.read_bytes() == b"new"


def test_backup_created(tmp_path: Path) -> None:
    path = tmp_path / "rules.json"
    path.write_text("old", encoding="utf-8")
    assert backup_file(path).exists()


def test_update_lock_prevents_parallel_update(tmp_path: Path) -> None:
    lock = UpdateLock(tmp_path / "update.lock")
    lock.acquire()
    with pytest.raises(RuntimeError):
        UpdateLock(tmp_path / "update.lock").acquire()
    lock.release()


def test_downloaded_artifact_not_executed() -> None:
    public_key, _signature = _keys()
    updater = Updater(["good"], public_key)
    assert hasattr(updater, "download_app_artifact")
