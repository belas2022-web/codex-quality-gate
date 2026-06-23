from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from codex_quality_gate.release_automation import (
    build_release_manifest,
    expected_tag_for_version,
    main,
)
from codex_quality_gate.updates.hashing import sha256_bytes
from codex_quality_gate.updates.manifest import verify_manifest
from codex_quality_gate.updates.models import UpdateManifest
from codex_quality_gate.updates.signatures import verify_ed25519


def _private_key_pair() -> tuple[str, str]:
    private = Ed25519PrivateKey.generate()
    private_bytes = private.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(private_bytes).decode(), base64.b64encode(public_bytes).decode()


def _write_dist(dist: Path) -> dict[str, bytes]:
    return _write_dist_for_version(dist, "0.1.0rc3")


def _write_dist_for_version(dist: Path, version: str) -> dict[str, bytes]:
    payloads = {
        f"codex_quality_gate-{version}-py3-none-any.whl": b"wheel",
        f"codex_quality_gate-{version}.tar.gz": b"sdist",
        "rules.json": b'{"rules": []}',
        "semgrep.yml": b"rules: []\n",
    }
    dist.mkdir()
    for name, payload in payloads.items():
        (dist / name).write_bytes(payload)
    return payloads


def test_expected_tag_for_version_handles_release_candidates_and_stable() -> None:
    assert expected_tag_for_version("0.1.0rc3") == "v0.1.0-rc3"
    assert expected_tag_for_version("0.1.0") == "v0.1.0"


def test_build_release_manifest_writes_signed_updater_manifest(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    payloads = _write_dist(dist)
    private_key, public_key = _private_key_pair()

    manifest_path = build_release_manifest(
        dist,
        version="0.1.0rc3",
        tag="v0.1.0-rc3",
        commit="abc123",
        repository="belas2022-web/codex-quality-gate",
        artifact_base_url="https://github.com/belas2022-web/codex-quality-gate/releases/download/v0.1.0-rc3",
        private_key_base64=private_key,
        created_at=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
        expires_at=datetime(2026, 7, 23, 12, 0, tzinfo=UTC),
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    update_manifest = UpdateManifest.from_dict(payload)

    assert manifest_path == dist / "latest.json"
    assert payload["version"] == "0.1.0rc3"
    assert payload["tag"] == "v0.1.0-rc3"
    assert payload["commit"] == "abc123"
    assert payload["signature_status"] == "signed"
    assert payload["rules_url"].endswith("/rules.json")
    assert payload["rules_sha256"] == sha256_bytes(payloads["rules.json"])
    assert verify_ed25519(payloads["rules.json"], payload["rules_signature"], public_key)
    assert payload["app_artifact_url"].endswith("/codex_quality_gate-0.1.0rc3-py3-none-any.whl")
    assert payload["app_artifact_sha256"] == sha256_bytes(
        payloads["codex_quality_gate-0.1.0rc3-py3-none-any.whl"]
    )
    assert verify_ed25519(
        payloads["codex_quality_gate-0.1.0rc3-py3-none-any.whl"],
        payload["app_artifact_signature"],
        public_key,
    )
    verify_manifest(update_manifest, public_key)

    sums = (dist / "SHA256SUMS").read_text(encoding="utf-8")
    for name, payload_bytes in payloads.items():
        assert f"{sha256_bytes(payload_bytes)}  {name}" in sums
    assert "latest.json" not in sums
    assert "SHA256SUMS" not in sums


def test_build_release_manifest_rejects_tag_version_mismatch(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _write_dist(dist)

    with pytest.raises(ValueError, match="does not match package version"):
        build_release_manifest(
            dist,
            version="0.1.0rc3",
            tag="v0.1.0-rc2",
            commit="abc123",
            repository="belas2022-web/codex-quality-gate",
        )


def test_build_release_manifest_requires_signature_for_stable(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _write_dist_for_version(dist, "0.1.0")

    with pytest.raises(ValueError, match="Stable releases require"):
        build_release_manifest(
            dist,
            version="0.1.0",
            tag="v0.1.0",
            commit="abc123",
            repository="belas2022-web/codex-quality-gate",
        )


def test_build_release_manifest_requires_real_public_key_for_stable(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _write_dist_for_version(dist, "0.1.0")
    private_key, _public_key = _private_key_pair()

    with pytest.raises(ValueError, match="real Ed25519 public key"):
        build_release_manifest(
            dist,
            version="0.1.0",
            tag="v0.1.0",
            commit="abc123",
            repository="belas2022-web/codex-quality-gate",
            public_key_base64="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
            private_key_base64=private_key,
        )


def test_build_release_manifest_rejects_mismatched_stable_public_key(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _write_dist_for_version(dist, "0.1.0")
    private_key, _public_key = _private_key_pair()
    _other_private_key, other_public_key = _private_key_pair()

    with pytest.raises(ValueError, match="does not match configured public key"):
        build_release_manifest(
            dist,
            version="0.1.0",
            tag="v0.1.0",
            commit="abc123",
            repository="belas2022-web/codex-quality-gate",
            public_key_base64=other_public_key,
            private_key_base64=private_key,
        )


def test_build_release_manifest_writes_unsigned_rc_manifest(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _write_dist(dist)

    manifest_path = build_release_manifest(
        dist,
        version="0.1.0rc3",
        tag="v0.1.0-rc3",
        commit="abc123",
        repository="belas2022-web/codex-quality-gate",
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["signature_status"] == "unsigned-rc"
    assert payload["manifest_signature"] == ""
    assert all(file["signature"] == "" for file in payload["files"])


def test_build_release_manifest_rejects_missing_update_bundle(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _write_dist(dist)
    (dist / "semgrep.yml").unlink()

    with pytest.raises(ValueError, match=r"semgrep\.yml"):
        build_release_manifest(
            dist,
            version="0.1.0rc3",
            tag="v0.1.0-rc3",
            commit="abc123",
            repository="belas2022-web/codex-quality-gate",
        )


def test_build_release_manifest_rejects_ambiguous_wheels(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _write_dist(dist)
    (dist / "codex_quality_gate-0.1.0rc3-extra-py3-none-any.whl").write_bytes(b"extra")

    with pytest.raises(ValueError, match="Expected exactly one artifact"):
        build_release_manifest(
            dist,
            version="0.1.0rc3",
            tag="v0.1.0-rc3",
            commit="abc123",
            repository="belas2022-web/codex-quality-gate",
        )


def test_release_automation_main_reads_private_key_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dist = tmp_path / "dist"
    _write_dist_for_version(dist, "0.1.0")
    private_key, public_key = _private_key_pair()
    monkeypatch.setenv("RELEASE_ED25519_PRIVATE_KEY_B64", private_key)
    monkeypatch.setattr(
        "codex_quality_gate.release_automation.DEFAULT_ED25519_PUBLIC_KEY_BASE64",
        public_key,
    )

    exit_code = main(
        [
            "--dist",
            str(dist),
            "--version",
            "0.1.0",
            "--tag",
            "v0.1.0",
            "--commit",
            "abc123",
            "--repository",
            "belas2022-web/codex-quality-gate",
            "--artifact-base-url",
            "https://github.com/belas2022-web/codex-quality-gate/releases/download/v0.1.0",
        ]
    )

    payload = json.loads((dist / "latest.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert str(dist / "latest.json") in capsys.readouterr().out
    assert payload["signature_status"] == "signed"
    verify_manifest(UpdateManifest.from_dict(payload), public_key)
