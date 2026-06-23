from __future__ import annotations

from typing import Any

from codex_quality_gate.chat_bridge.base import ChatMessage, HttpTransport
from codex_quality_gate.chat_bridge.permissions import ChatPermissions
from codex_quality_gate.chat_bridge.sanitizer import redact_secrets
from codex_quality_gate.core.errors import PolicyViolationError


class DiscordConnector:
    name = "discord"

    def __init__(
        self, token: str, permissions: ChatPermissions, transport: HttpTransport | None = None
    ) -> None:
        if token.lower().startswith("user:"):
            raise PolicyViolationError("Discord user tokens are forbidden")
        self.token = token
        self.permissions = permissions
        self.transport = transport or HttpTransport()

    def list_messages(self, source_id: str) -> list[ChatMessage]:
        self.permissions.require_read(source_id)
        response = self.transport.get(
            f"https://discord.com/api/v10/channels/{source_id}/messages",
            headers={"Authorization": f"Bot {self.token}"},
            params={"limit": 20},
        )
        response.raise_for_status()
        payload = response.json()
        items = payload if isinstance(payload, list) else []
        return [
            ChatMessage(
                "discord",
                source_id,
                str(item.get("author", {}).get("id", "unknown")),
                redact_secrets(str(item.get("content", ""))),
            )
            for item in items
            if isinstance(item, dict)
        ]

    def send_report(self, target_id: str, text: str) -> dict[str, Any]:
        self.permissions.require_write(target_id)
        response = self.transport.post(
            f"https://discord.com/api/v10/channels/{target_id}/messages",
            headers={"Authorization": f"Bot {self.token}"},
            json={"content": redact_secrets(text)},
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {"ok": True}
