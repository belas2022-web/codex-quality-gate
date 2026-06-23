from __future__ import annotations

import json
import zipfile
from pathlib import Path

from codex_quality_gate.chat_bridge.base import ChatMessage
from codex_quality_gate.chat_bridge.sanitizer import redact_secrets


def import_chatgpt_export(zip_path: str | Path) -> list[ChatMessage]:
    source = Path(zip_path)
    messages: list[ChatMessage] = []
    with zipfile.ZipFile(source) as archive:
        for member in archive.namelist():
            pure = Path(member)
            if pure.is_absolute() or ".." in pure.parts:
                raise ValueError("Unsafe path in chat export")
            if not member.endswith(".json"):
                continue
            payload = json.loads(archive.read(member).decode("utf-8"))
            if isinstance(payload, list):
                for item in payload:
                    if isinstance(item, dict):
                        messages.append(
                            ChatMessage(
                                "chatgpt_export",
                                source.name,
                                str(item.get("author", "unknown")),
                                redact_secrets(str(item.get("text", item.get("content", "")))),
                            )
                        )
    return messages
