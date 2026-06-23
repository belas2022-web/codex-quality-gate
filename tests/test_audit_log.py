from __future__ import annotations

from pathlib import Path

from codex_quality_gate.audit.audit_log import AuditLog
from codex_quality_gate.audit.events import AuditEvent


def test_audit_tail(tmp_path: Path) -> None:
    log = AuditLog(tmp_path / "audit.jsonl")
    log.write(AuditEvent("chat", {"token": "abcdef1234567890"}))
    assert log.tail(1)[0]["event_type"] == "chat"


def test_secrets_redacted_from_audit(tmp_path: Path) -> None:
    log = AuditLog(tmp_path / "audit.jsonl")
    log.write(AuditEvent("x", {"api_key": "1234567890123456"}))
    assert "1234567890123456" not in (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
