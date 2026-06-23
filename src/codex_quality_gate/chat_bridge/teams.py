from __future__ import annotations

from typing import Any

from codex_quality_gate.chat_bridge.base import ChatMessage, HttpTransport
from codex_quality_gate.chat_bridge.permissions import ChatPermissions
from codex_quality_gate.chat_bridge.sanitizer import redact_secrets


class TeamsConnector:
    name = "teams"

    def __init__(
        self,
        access_token: str,
        permissions: ChatPermissions,
        transport: HttpTransport | None = None,
    ) -> None:
        self.access_token = access_token
        self.permissions = permissions
        self.transport = transport or HttpTransport()

    def list_messages(self, source_id: str) -> list[ChatMessage]:
        self.permissions.require_read(source_id)
        response = self.transport.get(
            f"https://graph.microsoft.com/v1.0/chats/{source_id}/messages",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        response.raise_for_status()
        payload = response.json()
        values = payload.get("value", []) if isinstance(payload, dict) else []
        return [
            ChatMessage(
                "teams",
                source_id,
                str(item.get("from", {})),
                redact_secrets(str(item.get("body", {}).get("content", ""))),
            )
            for item in values
            if isinstance(item, dict)
        ]

    def send_report(self, target_id: str, text: str) -> dict[str, Any]:
        self.permissions.require_write(target_id)
        response = self.transport.post(
            f"https://graph.microsoft.com/v1.0/chats/{target_id}/messages",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={"body": {"contentType": "text", "content": redact_secrets(text)}},
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {"ok": True}
