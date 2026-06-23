from __future__ import annotations

from dataclasses import dataclass, field

from codex_quality_gate.core.errors import PolicyViolationError


@dataclass(frozen=True)
class ChatPermissions:
    allowed_read_ids: set[str] = field(default_factory=set)
    allowed_write_ids: set[str] = field(default_factory=set)
    writeback_allowed: bool = False
    send_full_code_allowed: bool = False

    def require_read(self, channel_id: str) -> None:
        if channel_id not in self.allowed_read_ids:
            raise PolicyViolationError(f"Read is not allowed for chat/channel: {channel_id}")

    def require_write(self, channel_id: str) -> None:
        if not self.writeback_allowed or channel_id not in self.allowed_write_ids:
            raise PolicyViolationError(f"Write-back is not allowed for chat/channel: {channel_id}")
