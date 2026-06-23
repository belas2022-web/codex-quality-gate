from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from codex_quality_gate.scanner.ignore import iter_project_files

CODE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".sh", ".ps1", ".sql"}


@dataclass(frozen=True)
class SourceFile:
    path: Path
    text: str


class FileScanner:
    def __init__(self, max_bytes: int = 1_000_000, extensions: set[str] | None = None) -> None:
        self.max_bytes = max_bytes
        self.extensions = extensions or CODE_EXTENSIONS

    def iter_files(self, root: str | Path) -> list[Path]:
        files: list[Path] = []
        for path in iter_project_files(root, self.extensions):
            try:
                if path.stat().st_size > self.max_bytes:
                    continue
            except OSError:
                continue
            files.append(path)
        return sorted(files)

    def read_file(self, path: Path) -> SourceFile:
        text = path.read_text(encoding="utf-8", errors="replace")
        return SourceFile(path=path, text=text)

    def scan(self, root: str | Path) -> list[SourceFile]:
        return [self.read_file(path) for path in self.iter_files(root)]
