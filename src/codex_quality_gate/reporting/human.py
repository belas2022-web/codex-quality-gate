from __future__ import annotations

from codex_quality_gate.core.result import ScanResult


def render_human(result: ScanResult) -> str:
    if not result.findings:
        return "No findings."
    return "\n".join(
        f"{finding.severity.value.upper()} {finding.path}:{finding.line}:{finding.column} "
        f"{finding.rule_id} {finding.message}"
        for finding in result.findings
    )
