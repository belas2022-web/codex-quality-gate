from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScanJob:
    project_name: str
