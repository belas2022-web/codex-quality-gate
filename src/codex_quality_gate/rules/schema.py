from __future__ import annotations

VALID_FIX_STRATEGIES = {"autofix", "manual", "review_required", "blocked"}
VALID_SEVERITIES = {"critical", "error", "warning", "info"}
REQUIRED_CATALOG_FIELDS = {"schema_version", "rules_version", "minimum_app_version", "rules"}
REQUIRED_RULE_FIELDS = {
    "id",
    "title",
    "severity",
    "category",
    "languages",
    "extensions",
    "regex",
    "message",
    "repair_hint",
    "fix_strategy",
    "tags",
}


def validate_catalog_payload(payload: dict[str, object]) -> None:
    missing = REQUIRED_CATALOG_FIELDS.difference(payload)
    if missing:
        raise ValueError(f"Missing required catalog fields: {', '.join(sorted(missing))}")
    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported rules schema_version")
    if not isinstance(payload.get("rules"), list):
        raise TypeError("Rules payload must contain a rules list")


def validate_rule_payload(payload: dict[str, object]) -> None:
    missing = REQUIRED_RULE_FIELDS.difference(payload)
    if missing:
        raise ValueError(f"Missing required rule fields: {', '.join(sorted(missing))}")
    if str(payload["severity"]) not in VALID_SEVERITIES:
        raise ValueError(f"Invalid rule severity: {payload['severity']}")
    if str(payload["fix_strategy"]) not in VALID_FIX_STRATEGIES:
        raise ValueError(f"Invalid rule fix_strategy: {payload['fix_strategy']}")
    if not payload["repair_hint"]:
        raise ValueError(f"Rule {payload['id']} must include repair_hint")
