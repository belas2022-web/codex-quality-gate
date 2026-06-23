from __future__ import annotations

from codex_quality_gate.rules.models import Rule


def export_semgrep_rules(rules: list[Rule]) -> str:
    lines = ["rules:"]
    for rule in rules:
        lines.extend(
            [
                f"  - id: codex-quality-gate.{rule.id}",
                "    patterns:",
                f"      - pattern-regex: {rule.pattern!r}",
                f"    message: {rule.message!r}",
                f"    severity: {rule.severity.value.upper()}",
                "    languages: [generic]",
            ]
        )
    return "\n".join(lines) + "\n"
