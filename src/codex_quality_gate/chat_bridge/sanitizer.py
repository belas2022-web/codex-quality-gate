from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, TypeVar, cast

T = TypeVar("T")

SECRET_KEY_RE = re.compile(
    r"(?i)(token|secret|password|api[_-]?key|apikey|authorization|bearer|"
    r"access[_-]?token|refresh[_-]?token)"
)
SAFE_SECRET_NAMED_KEYS = {"secrets_exposed"}

URL_CREDENTIAL_RE = re.compile(r"(?P<scheme>[a-z][a-z0-9+.-]*://)(?P<credentials>[^/@\s]+@)")
KEY_VALUE_SECRET_RE = re.compile(
    r"(?i)\b(?P<key>token|secret|password|api[_-]?key|apikey|authorization|bearer|"
    r"access[_-]?token|refresh[_-]?token)\b"
    r"(?P<separator>\s*(?:=|:|\s)\s*)"
    r"(?P<prefix>Bearer\s+)?"
    r"['\"]?"
    r"(?P<secret>[A-Za-z0-9._~+/=-][A-Za-z0-9._~+/=-]{5,})"
    r"['\"]?"
)
BARE_SECRET_PATTERNS = (
    re.compile(r"(?i)\bsecret-token-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bsk_(?:test|live)_[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9_]{16,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{16,}\b"),
    re.compile(r"\bxox[abp]-[A-Za-z0-9-]{12,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{8,}\b"),
)


def redact_secrets(text: str) -> str:
    if KEY_VALUE_SECRET_RE.fullmatch(text.strip()):
        return "[REDACTED]"
    return redact_secret_text(text)


def redact_secret_text(value: str) -> str:
    redacted = URL_CREDENTIAL_RE.sub(r"\g<scheme>[REDACTED]@", value)
    redacted = KEY_VALUE_SECRET_RE.sub(_redact_key_value_match, redacted)
    for pattern in BARE_SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def redact_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, item in value.items():
        key_text = str(key)
        if key_text.lower() not in SAFE_SECRET_NAMED_KEYS and SECRET_KEY_RE.search(key_text):
            redacted[key_text] = "[REDACTED]"
        else:
            redacted[key_text] = redact_nested(item)
    return redacted


def redact_nested(value: Any) -> Any:
    if isinstance(value, str):
        return redact_secret_text(value)
    if isinstance(value, Mapping):
        return redact_mapping(value)
    if isinstance(value, list):
        return [redact_nested(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_nested(item) for item in value)
    return value


def sanitize_api_response(value: T) -> T:
    return cast(T, redact_nested(value))


def _redact_key_value_match(match: re.Match[str]) -> str:
    key = match.group("key")
    separator = match.group("separator")
    prefix = match.group("prefix") or ""
    return f"{key}{separator}{prefix}[REDACTED]"
