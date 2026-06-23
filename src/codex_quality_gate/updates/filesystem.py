from __future__ import annotations

import os
import shutil
from pathlib import Path


def atomic_write(path: str | Path, data: bytes) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + ".tmp")
    temp.write_bytes(data)
    os.replace(temp, target)


def backup_file(path: str | Path) -> Path:
    source = Path(path)
    backup = source.with_suffix(source.suffix + ".bak")
    if source.exists():
        shutil.copy2(source, backup)
    return backup


class UpdateLock:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._handle: int | None = None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._handle = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise RuntimeError(f"Update lock already exists: {self.path}") from exc

    def release(self) -> None:
        if self._handle is not None:
            os.close(self._handle)
            self._handle = None
        if self.path.exists():
            self.path.unlink()

    def __enter__(self) -> UpdateLock:
        self.acquire()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.release()
