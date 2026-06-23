from __future__ import annotations

from typing import Any

from codex_quality_gate.chat_bridge.base import ChatMessage, HttpTransport
from codex_quality_gate.chat_bridge.permissions import ChatPermissions
from codex_quality_gate.chat_bridge.sanitizer import redact_secrets


class OpenAIConversationsConnector:
    name = "openai_conversations"

    def __init__(
        self, api_key: str, permissions: ChatPermissions, transport: HttpTransport | None = None
    ) -> None:
        self.api_key = api_key
        self.permissions = permissions
        self.transport = transport or HttpTransport()

    def list_messages(self, source_id: str) -> list[ChatMessage]:
        self.permissions.require_read(source_id)
        response = self.transport.get(
            f"https://api.openai.com/v1/conversations/{source_id}/items",
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        response.raise_for_status()
        payload = response.json()
        items = payload.get("data", []) if isinstance(payload, dict) else []
        return [
            ChatMessage(
                "openai_conversations",
                source_id,
                str(item.get("role", "unknown")),
                redact_secrets(str(item.get("content", ""))),
            )
            for item in items
            if isinstance(item, dict)
        ]

    def send_report(self, target_id: str, text: str) -> dict[str, Any]:
        self.permissions.require_write(target_id)
        response = self.transport.post(
            f"https://api.openai.com/v1/conversations/{target_id}/items",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"items": [{"type": "message", "role": "user", "content": redact_secrets(text)}]},
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {"ok": True}
