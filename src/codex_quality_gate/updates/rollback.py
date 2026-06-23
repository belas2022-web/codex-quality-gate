from __future__ import annotations

import shutil
from pathlib import Path

from codex_quality_gate.core.errors import SecurityVerificationError
from codex_quality_gate.updates.security import reject_symlink_target


def rollback_file(
    target: str | Path,
    backup: str | Path,
    *,
    base_dir: str | Path,
    backup_base_dir: str | Path | None = None,
) -> None:
    destination = _resolve_inside_base(base_dir, target)
    source = _resolve_inside_base(backup_base_dir or base_dir, backup)
    if not source.exists():
        raise FileNotFoundError(f"Backup not found: {source}")
    reject_symlink_target(destination)
    reject_symlink_target(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _resolve_inside_base(base_dir: str | Path, candidate: str | Path) -> Path:
    base = Path(base_dir).resolve()
    raw = Path(candidate)
    resolved = raw.resolve() if raw.is_absolute() else (base / raw).resolve()
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise SecurityVerificationError(
            f"Rollback path escapes base directory: {candidate}"
        ) from exc
    return resolved
