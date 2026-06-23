from __future__ import annotations

from codex_quality_gate.chat_bridge.base import ChatMessage


def summarize_messages(messages: list[ChatMessage]) -> dict[str, int]:
    return {"messages": len(messages)}
