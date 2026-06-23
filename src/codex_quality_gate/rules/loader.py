from __future__ import annotations

import json
from pathlib import Path

from codex_quality_gate.core.result import Severity
from codex_quality_gate.rules.models import Rule
from codex_quality_gate.rules.schema import validate_catalog_payload, validate_rule_payload
from codex_quality_gate.rules.validator import validate_rules


def load_rules(path: str | Path) -> list[Rule]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("Rules payload must be an object")
    validate_catalog_payload(payload)
    raw_rules = payload["rules"]
    if not isinstance(raw_rules, list):
        raise TypeError("Rules payload must contain a rules list")
    rules: list[Rule] = []
    for item in raw_rules:
        if not isinstance(item, dict):
            raise TypeError("Each rule must be an object")
        validate_rule_payload(item)
        languages = item["languages"]
        extensions = item["extensions"]
        tags = item["tags"]
        if (
            not isinstance(languages, list)
            or not isinstance(extensions, list)
            or not isinstance(tags, list)
        ):
            raise TypeError("Rule languages, extensions, and tags must be lists")
        rules.append(
            Rule(
                id=str(item["id"]),
                pattern=str(item["regex"]),
                message=str(item["message"]),
                severity=Severity(str(item["severity"])),
                category=str(item["category"]),
                extensions=tuple(str(value) for value in extensions),
                title=str(item["title"]),
                languages=tuple(str(value) for value in languages),
                repair_hint=str(item["repair_hint"]),
                fix_strategy=str(item["fix_strategy"]),
                tags=tuple(str(value) for value in tags),
            )
        )
    validate_rules(rules)
    return rules
