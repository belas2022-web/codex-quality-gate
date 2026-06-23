from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StoredFinding:
    run_id: int
    rule_id: str
    path: str
    severity: str
    message: str
