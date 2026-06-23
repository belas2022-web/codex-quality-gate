from __future__ import annotations

from codex_quality_gate.core.result import ScanResult


def render_markdown(result: ScanResult) -> str:
    lines = [
        "# codex-quality-gate report",
        "",
        "| Severity | Rule | Location | Message |",
        "| --- | --- | --- | --- |",
    ]
    for finding in result.findings:
        location = f"{finding.path}:{finding.line}"
        lines.append(
            f"| {finding.severity.value} | {finding.rule_id} | {location} | {finding.message} |"
        )
    return "\n".join(lines) + "\n"
