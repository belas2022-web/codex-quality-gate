from __future__ import annotations

import argparse
import base64
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from packaging.version import Version

from codex_quality_gate.constants import DEFAULT_ED25519_PUBLIC_KEY_BASE64
from codex_quality_gate.updates.filesystem import atomic_write
from codex_quality_gate.updates.hashing import sha256_bytes
from codex_quality_gate.updates.models import UpdateManifest

_PLACEHOLDER_ED25519_PUBLIC_KEYS = {
    "",
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
}


@dataclass(frozen=True)
class ReleaseArtifact:
    name: str
    sha256: str
    size: int
    url: str
    signature: str


def expected_tag_for_version(version: str) -> str:
    parsed = Version(version)
    base = f"v{parsed.major}.{parsed.minor}.{parsed.micro}"
    if parsed.pre and parsed.pre[0] == "rc":
        return f"{base}-rc{parsed.pre[1]}"
    return base


def build_release_manifest(
    dist_dir: Path,
    *,
    version: str,
    tag: str,
    commit: str,
    repository: str,
    artifact_base_url: str = "",
    public_key_base64: str = "",
    private_key_base64: str = "",
    created_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> Path:
    expected_tag = expected_tag_for_version(version)
    if tag != expected_tag:
        raise ValueError(f"Release tag {tag!r} does not match package version {version!r}")

    private_key = _load_private_key(private_key_base64) if private_key_base64 else None
    if Version(version).pre is None and private_key is None:
        raise ValueError("Stable releases require RELEASE_ED25519_PRIVATE_KEY_B64")
    if Version(version).pre is None and private_key is not None:
        _validate_stable_signing_key(
            public_key_base64 or DEFAULT_ED25519_PUBLIC_KEY_BASE64,
            private_key,
        )

    dist_dir = dist_dir.resolve()
    wheel = _single_artifact(dist_dir, f"*{version}*.whl")
    sdist = _single_artifact(dist_dir, f"*{version}*.tar.gz")
    rules = _required_artifact(dist_dir / "rules.json")
    semgrep = _required_artifact(dist_dir / "semgrep.yml")

    artifacts = [
        _artifact(wheel, artifact_base_url, private_key),
        _artifact(sdist, artifact_base_url, private_key),
        _artifact(rules, artifact_base_url, private_key),
        _artifact(semgrep, artifact_base_url, private_key),
    ]
    _write_sha256sums(dist_dir, artifacts)

    created = _format_timestamp(created_at or datetime.now(UTC))
    expires = _format_timestamp(expires_at or datetime.now(UTC) + timedelta(days=30))
    artifact_by_name = {artifact.name: artifact for artifact in artifacts}
    rules_artifact = artifact_by_name["rules.json"]
    app_artifact = artifact_by_name[wheel.name]

    manifest = {
        "schema_version": 1,
        "version": version,
        "tag": tag,
        "commit": commit,
        "repository": repository,
        "created_at": created,
        "expires_at": expires,
        "rules_url": rules_artifact.url,
        "rules_sha256": rules_artifact.sha256,
        "rules_signature": rules_artifact.signature,
        "app_artifact_url": app_artifact.url,
        "app_artifact_sha256": app_artifact.sha256,
        "app_artifact_signature": app_artifact.signature,
        "signature_algorithm": "Ed25519",
        "signature_status": "signed" if private_key else "unsigned-rc",
        "files": [artifact.__dict__ for artifact in artifacts],
        "manifest_signature": "",
    }
    if private_key is not None:
        update_manifest = UpdateManifest.from_dict(manifest)
        manifest["manifest_signature"] = _sign(update_manifest.canonical_bytes(), private_key)

    manifest_path = dist_dir / "latest.json"
    manifest_payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    atomic_write(manifest_path, manifest_payload.encode())
    return manifest_path


def _single_artifact(dist_dir: Path, pattern: str) -> Path:
    matches = sorted(dist_dir.glob(pattern))
    if len(matches) != 1:
        names = ", ".join(path.name for path in matches) or "none"
        raise ValueError(f"Expected exactly one artifact matching {pattern!r}; found {names}")
    return matches[0]


def _required_artifact(path: Path) -> Path:
    if not path.is_file():
        raise ValueError(f"Required release artifact is missing: {path.name}")
    return path


def _artifact(
    path: Path,
    artifact_base_url: str,
    private_key: Ed25519PrivateKey | None,
) -> ReleaseArtifact:
    payload = path.read_bytes()
    return ReleaseArtifact(
        name=path.name,
        sha256=sha256_bytes(payload),
        size=len(payload),
        url=_artifact_url(path.name, artifact_base_url),
        signature=_sign(payload, private_key) if private_key else "",
    )


def _artifact_url(name: str, artifact_base_url: str) -> str:
    if not artifact_base_url:
        return name
    return f"{artifact_base_url.rstrip('/')}/{name}"


def _write_sha256sums(dist_dir: Path, artifacts: list[ReleaseArtifact]) -> None:
    lines = [
        f"{artifact.sha256}  {artifact.name}"
        for artifact in sorted(artifacts, key=lambda item: item.name)
    ]
    atomic_write(dist_dir / "SHA256SUMS", ("\n".join(lines) + "\n").encode())


def _load_private_key(private_key_base64: str) -> Ed25519PrivateKey:
    private_bytes = base64.b64decode(private_key_base64)
    return Ed25519PrivateKey.from_private_bytes(private_bytes)


def _validate_stable_signing_key(
    public_key_base64: str,
    private_key: Ed25519PrivateKey,
) -> None:
    if public_key_base64 in _PLACEHOLDER_ED25519_PUBLIC_KEYS:
        raise ValueError("Stable releases require a real Ed25519 public key")

    configured_public_key = base64.b64decode(public_key_base64)
    signing_public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    if configured_public_key != signing_public_key:
        raise ValueError("Stable release private key does not match configured public key")


def _sign(payload: bytes, private_key: Ed25519PrivateKey) -> str:
    return base64.b64encode(private_key.sign(payload)).decode()


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build release metadata for codex-quality-gate.")
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--version", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--artifact-base-url", default="")
    parser.add_argument("--private-key-env", default="RELEASE_ED25519_PRIVATE_KEY_B64")
    args = parser.parse_args(argv)

    manifest_path = build_release_manifest(
        args.dist,
        version=args.version,
        tag=args.tag,
        commit=args.commit,
        repository=args.repository,
        artifact_base_url=args.artifact_base_url,
        private_key_base64=os.environ.get(args.private_key_env, ""),
    )
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
