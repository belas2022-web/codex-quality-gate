from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class UpdateSource:
    type: str
    name: str
    enabled: bool
    priority: int
    config: dict[str, Any]


class SourceClient(Protocol):
    def latest(self) -> dict[str, Any]: ...
