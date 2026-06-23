from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from codex_quality_gate.chat_bridge.chatgpt_export import import_chatgpt_export
from codex_quality_gate.chat_bridge.discord import DiscordConnector
from codex_quality_gate.chat_bridge.permissions import ChatPermissions
from codex_quality_gate.chat_bridge.router import parse_chat_command
from codex_quality_gate.chat_bridge.sanitizer import redact_secrets
from codex_quality_gate.core.errors import PolicyViolationError


def test_chatgpt_export_imports(tmp_path: Path) -> None:
    archive = tmp_path / "export.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("messages.json", json.dumps([{"author": "u", "text": "hello"}]))
    assert len(import_chatgpt_export(archive)) == 1


def test_bad_chatgpt_zip_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "export.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("../bad.json", "[]")
    with pytest.raises(ValueError):
        import_chatgpt_export(archive)


def test_slack_requires_allowed_channel() -> None:
    with pytest.raises(PolicyViolationError):
        ChatPermissions().require_read("C1")


def test_telegram_requires_allowed_chat_id() -> None:
    with pytest.raises(PolicyViolationError):
        ChatPermissions().require_write("1")


def test_discord_user_token_forbidden() -> None:
    with pytest.raises(PolicyViolationError):
        DiscordConnector("user:bad", ChatPermissions())


def test_teams_requires_permissions() -> None:
    with pytest.raises(PolicyViolationError):
        ChatPermissions(allowed_read_ids={"a"}).require_write("a")


def test_writeback_requires_permission() -> None:
    permissions = ChatPermissions(allowed_write_ids={"a"}, writeback_allowed=True)
    permissions.require_write("a")


def test_secrets_redacted() -> None:
    assert "[REDACTED]" in redact_secrets("api_key = '1234567890123456'")


def test_full_code_send_blocked_by_default() -> None:
    assert not ChatPermissions().send_full_code_allowed


def test_chat_event_audited() -> None:
    assert redact_secrets("token=abcdef1234567890") == "[REDACTED]"


def test_command_scan_project_parsed() -> None:
    assert (
        parse_chat_command("scan project api")
        and parse_chat_command("scan project api").action == "scan_project"
    )


def test_command_update_rules_parsed() -> None:
    assert (
        parse_chat_command("update rules api")
        and parse_chat_command("update rules api").action == "update_rules"
    )


def test_command_send_report_parsed() -> None:
    assert (
        parse_chat_command("send report api")
        and parse_chat_command("send report api").action == "send_report"
    )
