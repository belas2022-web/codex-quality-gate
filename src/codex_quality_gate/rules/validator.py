from __future__ import annotations

import re

from codex_quality_gate.rules.models import Rule
from codex_quality_gate.rules.schema import VALID_FIX_STRATEGIES


def validate_rules(rules: list[Rule]) -> None:
    if not rules:
        raise ValueError("Rules catalog must not be empty")
    ids: set[str] = set()
    for rule in rules:
        if rule.id in ids:
            raise ValueError(f"Duplicate rule id: {rule.id}")
        ids.add(rule.id)
        if not rule.id or not rule.pattern or not rule.message or not rule.repair_hint:
            raise ValueError("Rule id, pattern, message, and repair_hint are required")
        if rule.fix_strategy not in VALID_FIX_STRATEGIES:
            raise ValueError(f"Invalid fix strategy for {rule.id}: {rule.fix_strategy}")
        try:
            re.compile(rule.pattern)
        except re.error as exc:
            raise ValueError(f"Invalid rule regex for {rule.id}: {exc}") from exc
