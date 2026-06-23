from __future__ import annotations

from codex_quality_gate.core.errors import PolicyViolationError


def validate_writeback(allowed: bool) -> None:
    if not allowed:
        raise PolicyViolationError("Chat write-back permission is required")


def validate_full_code_send(allowed: bool) -> None:
    if not allowed:
        raise PolicyViolationError("Sending full source code is blocked by default")
