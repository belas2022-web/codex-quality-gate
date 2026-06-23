from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class ChatCommand:
    action: str
    project: str


COMMAND_PATTERNS: tuple[tuple[str, str], ...] = (
    ("scan_project", r"^scan\s+project\s+(?P<target>[\w.-]+)$"),
    ("bootstrap_project", r"^bootstrap\s+project\s+(?P<target>[\w.-]+)$"),
    ("update_rules", r"^update\s+rules(?:\s+for)?\s+(?P<target>[\w.-]+)$"),
    ("show_findings", r"^show\s+findings\s+(?P<target>[\w.-]+)$"),
    ("send_report", r"^send\s+report\s+(?P<target>[\w.-]+)$"),
    ("explain_finding", r"^explain\s+finding\s+(?P<target>[\w.-]+)$"),
    ("approve_autofix", r"^approve\s+safe\s+autofix\s+run\s+(?P<target>\d+)$"),
    ("scan_project", r"^проверь\s+проект\s+(?P<target>[\w.-]+)$"),
    ("bootstrap_project", r"^установи\s+проверки\s+для\s+(?P<target>[\w.-]+)$"),
    ("update_rules", r"^обнови\s+правила\s+для\s+(?P<target>[\w.-]+)$"),
    ("show_findings", r"^покажи\s+ошибки\s+(?P<target>[\w.-]+)$"),
    ("send_report", r"^отправь\s+отч[её]т\s+(?P<target>[\w.-]+)$"),
    ("explain_finding", r"^объясни\s+ошибку\s+(?P<target>[\w.-]+)$"),
    ("approve_autofix", r"^разрешаю\s+safe\s+autofix\s+для\s+run\s+(?P<target>\d+)$"),
)


def parse_chat_command(text: str) -> ChatCommand | None:
    for candidate in _text_variants(text):
        normalized = " ".join(candidate.strip().split())
        for action, pattern in COMMAND_PATTERNS:
            match = re.match(pattern, normalized, flags=re.IGNORECASE)
            if match is not None:
                return ChatCommand(action, match.group("target"))
    return None


def _text_variants(text: str) -> Iterable[str]:
    yield text
    try:
        recovered = text.encode("cp1251").decode("utf-8")
    except UnicodeError:
        return
    if recovered != text:
        yield recovered
