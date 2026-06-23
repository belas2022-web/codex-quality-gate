from __future__ import annotations

from pathlib import Path


def workspace_state_dir(root: str | Path) -> Path:
    return Path(root).resolve() / ".codex-quality-gate"
