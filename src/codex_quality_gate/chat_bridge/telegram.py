from __future__ import annotations

from typing import Any

from codex_quality_gate.chat_bridge.base import ChatMessage, HttpTransport
from codex_quality_gate.chat_bridge.permissions import ChatPermissions
from codex_quality_gate.chat_bridge.sanitizer import redact_secrets


class TelegramConnector:
    name = "telegram"

    def __init__(
        self, token: str, permissions: ChatPermissions, transport: HttpTransport | None = None
    ) -> None:
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.permissions = permissions
        self.transport = transport or HttpTransport()

    def list_messages(self, source_id: str) -> list[ChatMessage]:
        self.permissions.require_read(source_id)
        response = self.transport.get(f"{self.base_url}/getUpdates")
        response.raise_for_status()
        payload = response.json()
        updates = payload.get("result", []) if isinstance(payload, dict) else []
        messages: list[ChatMessage] = []
        for item in updates:
            if not isinstance(item, dict):
                continue
            message = item.get("message")
            if not isinstance(message, dict):
                continue
            chat = message.get("chat")
            if isinstance(chat, dict) and str(chat.get("id")) == source_id:
                messages.append(
                    ChatMessage(
                        "telegram",
                        source_id,
                        str(message.get("from", {})),
                        redact_secrets(str(message.get("text", ""))),
                    )
                )
        return messages

    def send_report(self, target_id: str, text: str) -> dict[str, Any]:
        self.permissions.require_write(target_id)
        response = self.transport.post(
            f"{self.base_url}/sendMessage",
            json={"chat_id": target_id, "text": redact_secrets(text)},
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {"ok": False}
