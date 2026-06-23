from __future__ import annotations

import os
from pathlib import Path


class ProjectLock:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._handle: int | None = None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._handle = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise RuntimeError(f"Project is already locked: {self.path}") from exc

    def release(self) -> None:
        if self._handle is not None:
            os.close(self._handle)
            self._handle = None
        if self.path.exists():
            self.path.unlink()

    def __enter__(self) -> ProjectLock:
        self.acquire()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.release()
