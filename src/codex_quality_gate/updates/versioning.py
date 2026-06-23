from __future__ import annotations

from packaging.version import Version


def is_newer(candidate: str, current: str) -> bool:
    return Version(candidate) > Version(current)


def reject_downgrade(candidate: str, current: str) -> None:
    if Version(candidate) < Version(current):
        raise ValueError(f"Downgrade rejected: {candidate} < {current}")
