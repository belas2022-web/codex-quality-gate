from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    name: str
    payload: dict[str, object]


class JobQueue:
    def __init__(self) -> None:
        self._items: deque[Job] = deque()

    def push(self, job: Job) -> None:
        self._items.append(job)

    def pop(self) -> Job | None:
        if not self._items:
            return None
        return self._items.popleft()
