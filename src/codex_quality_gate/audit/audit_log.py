from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from codex_quality_gate.audit.events import AuditEvent
from codex_quality_gate.chat_bridge.sanitizer import redact_nested


def _redact_payload(value: Any) -> Any:
    return redact_nested(value)


class AuditLog:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write(self, event: AuditEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "event_type": event.event_type,
            "payload": _redact_payload(event.payload),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def tail(self, limit: int = 20) -> list[dict[str, object]]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()[-limit:]
        return [json.loads(line) for line in lines if line.strip()]
