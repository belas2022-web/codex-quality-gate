from __future__ import annotations

import re
from pathlib import Path

from codex_quality_gate.core.result import Finding
from codex_quality_gate.rules.loader import load_rules
from codex_quality_gate.rules.models import Rule
from codex_quality_gate.rules.validator import validate_rules

DEFAULT_RULES_PATH = Path(__file__).resolve().parents[1] / "data" / "default_rules.json"


def default_rules() -> list[Rule]:
    return load_rules(DEFAULT_RULES_PATH)


class RuleEngine:
    def __init__(self, rules: list[Rule] | None = None) -> None:
        self.rules = rules or default_rules()
        validate_rules(self.rules)

    def scan_text(self, path: str | Path, text: str) -> list[Finding]:
        source_path = str(path)
        suffix = Path(path).suffix.lower()
        findings: list[Finding] = []
        for rule in self.rules:
            if suffix and suffix not in rule.extensions:
                continue
            compiled = re.compile(rule.pattern)
            for line_number, line in enumerate(text.splitlines(), start=1):
                match = compiled.search(line)
                if match is None:
                    continue
                finding_id = f"{rule.id}:{source_path}:{line_number}:{match.start() + 1}"
                findings.append(
                    Finding(
                        id=finding_id,
                        path=source_path,
                        line=line_number,
                        column=match.start() + 1,
                        severity=rule.severity,
                        message=rule.message,
                        rule_id=rule.id,
                        category=rule.category,
                        matched_text=match.group(0),
                    )
                )
        return findings
