from __future__ import annotations

from dataclasses import dataclass

from codex_quality_gate.core.result import Severity


@dataclass(frozen=True)
class Rule:
    id: str
    pattern: str
    message: str
    severity: Severity
    category: str
    extensions: tuple[str, ...] = (".py", ".js", ".jsx", ".ts", ".tsx", ".sh", ".ps1", ".sql")
    title: str = ""
    languages: tuple[str, ...] = ()
    repair_hint: str = ""
    fix_strategy: str = "manual"
    tags: tuple[str, ...] = ()
