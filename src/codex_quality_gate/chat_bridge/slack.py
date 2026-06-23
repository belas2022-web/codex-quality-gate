from __future__ import annotations

from typing import Any

from codex_quality_gate.chat_bridge.base import ChatMessage, HttpTransport
from codex_quality_gate.chat_bridge.permissions import ChatPermissions
from codex_quality_gate.chat_bridge.sanitizer import redact_secrets


class SlackConnector:
    name = "slack"

    def __init__(
        self, token: str, permissions: ChatPermissions, transport: HttpTransport | None = None
    ) -> None:
        self.token = token
        self.permissions = permissions
        self.transport = transport or HttpTransport()

    def list_messages(self, source_id: str) -> list[ChatMessage]:
        self.permissions.require_read(source_id)
        response = self.transport.get(
            "https://slack.com/api/conversations.history",
            headers={"Authorization": f"Bearer {self.token}"},
            params={"channel": source_id, "limit": 20},
        )
        response.raise_for_status()
        payload = response.json()
        messages = payload.get("messages", []) if isinstance(payload, dict) else []
        return [
            ChatMessage(
                "slack",
                source_id,
                str(item.get("user", "unknown")),
                redact_secrets(str(item.get("text", ""))),
            )
            for item in messages
            if isinstance(item, dict)
        ]

    def send_report(self, target_id: str, text: str) -> dict[str, Any]:
        self.permissions.require_write(target_id)
        response = self.transport.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"channel": target_id, "text": redact_secrets(text)},
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {"ok": False}
