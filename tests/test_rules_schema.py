from __future__ import annotations

import pytest

from codex_quality_gate.rules.schema import validate_catalog_payload, validate_rule_payload


def test_rule_schema_accepts_required_catalog_shape() -> None:
    validate_catalog_payload(
        {
            "schema_version": 1,
            "rules_version": "2026.06.22",
            "minimum_app_version": "0.1.0",
            "rules": [],
        }
    )


def test_rule_schema_rejects_missing_repair_hint() -> None:
    payload: dict[str, object] = {
        "id": "X",
        "title": "X",
        "severity": "warning",
        "category": "demo",
        "languages": ["python"],
        "extensions": [".py"],
        "regex": "x",
        "message": "x",
        "fix_strategy": "manual",
        "tags": ["demo"],
    }
    with pytest.raises(ValueError):
        validate_rule_payload(payload)
