from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from packaging.version import Version

from codex_quality_gate.core.errors import SecurityVerificationError


def validate_https_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise SecurityVerificationError(f"Only HTTPS update URLs are allowed: {url}")
    if not parsed.netloc:
        raise SecurityVerificationError(f"Update URL must include a host: {url}")


def validate_allowed_domain(url: str, allowed_domains: list[str]) -> None:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if not _host_allowed(host, allowed_domains):
        raise SecurityVerificationError(f"Update URL host is not allowlisted: {host}")


def validate_update_url(url: str, allowed_domains: list[str]) -> None:
    validate_https_url(url)
    validate_allowed_domain(url, allowed_domains)


def validate_no_redirect_to_untrusted_domain(
    original_url: str,
    final_url: str,
    allowed_domains: list[str],
) -> None:
    validate_update_url(original_url, allowed_domains)
    validate_update_url(final_url, allowed_domains)
    original_host = urlparse(original_url).hostname or ""
    final_host = urlparse(final_url).hostname or ""
    if not _host_allowed(final_host, [original_host, *allowed_domains]):
        raise SecurityVerificationError(
            f"Update redirect changed to an untrusted host: {original_host} -> {final_host}"
        )


def validate_file_size(size_bytes: int, max_size_bytes: int) -> None:
    if size_bytes < 0:
        raise SecurityVerificationError("Update payload size cannot be negative")
    if size_bytes > max_size_bytes:
        raise SecurityVerificationError(
            f"Update payload is too large: {size_bytes} > {max_size_bytes}"
        )


def reject_replay_manifest(manifest: dict[str, object], local_history: Iterable[str]) -> None:
    manifest_id = str(
        manifest.get("manifest_id")
        or manifest.get("rules_version")
        or manifest.get("version")
        or ""
    )
    if not manifest_id:
        raise SecurityVerificationError("Manifest must include a replay identifier")
    if manifest_id in {str(item) for item in local_history}:
        raise SecurityVerificationError(f"Replayed update manifest rejected: {manifest_id}")


def reject_expired_manifest(
    manifest: dict[str, object],
    *,
    now: datetime | None = None,
) -> None:
    raw_expires_at = manifest.get("expires_at")
    if not raw_expires_at:
        raise SecurityVerificationError("Manifest must include expires_at")
    expires_at = _parse_datetime(str(raw_expires_at))
    current = now or datetime.now(UTC)
    if expires_at <= current:
        raise SecurityVerificationError(f"Update manifest has expired: {raw_expires_at}")


def reject_downgrade(remote_version: str, local_version: str) -> None:
    if Version(remote_version) < Version(local_version):
        raise SecurityVerificationError(
            f"Downgrade rejected: remote {remote_version} < local {local_version}"
        )


def safe_join(base: str | Path, user_path: str | Path) -> Path:
    base_path = Path(base).resolve()
    candidate = Path(user_path)
    if candidate.is_absolute():
        raise SecurityVerificationError(f"Absolute update path is not allowed: {candidate}")
    resolved = (base_path / candidate).resolve()
    try:
        resolved.relative_to(base_path)
    except ValueError as exc:
        raise SecurityVerificationError(f"Update path escapes base directory: {user_path}") from exc
    return resolved


def reject_symlink_target(path: str | Path) -> None:
    target = Path(path)
    if target.exists() and target.is_symlink():
        raise SecurityVerificationError(f"Refusing to overwrite symlink update target: {target}")
    for parent in target.parents:
        if parent.exists() and parent.is_symlink():
            raise SecurityVerificationError(f"Refusing update through symlink parent: {parent}")


def _host_allowed(host: str, allowed_domains: list[str]) -> bool:
    normalized = host.lower().rstrip(".")
    for domain in allowed_domains:
        allowed = domain.lower().rstrip(".")
        if normalized == allowed or normalized.endswith(f".{allowed}"):
            return True
    return False


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise SecurityVerificationError(f"Invalid manifest expires_at: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
