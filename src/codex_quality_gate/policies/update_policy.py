from __future__ import annotations

from codex_quality_gate.updates.security import validate_update_url


def validate_source_url(url: str, allowed_domains: list[str]) -> None:
    validate_update_url(url, allowed_domains)
