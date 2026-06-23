from __future__ import annotations

from pathlib import Path

from codex_quality_gate.updates.security import reject_symlink_target, safe_join


def cache_payload(cache_dir: str | Path, name: str, payload: bytes) -> Path:
    path = safe_join(cache_dir, name)
    reject_symlink_target(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path
