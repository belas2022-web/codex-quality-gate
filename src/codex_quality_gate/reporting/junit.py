from __future__ import annotations

from html import escape

from codex_quality_gate.core.result import ScanResult


def render_junit(result: ScanResult) -> str:
    failures = len(result.findings)
    lines = [f'<testsuite name="codex-quality-gate" tests="{failures}" failures="{failures}">']
    for finding in result.findings:
        lines.append(
            f'  <testcase classname="{escape(finding.category)}" name="{escape(finding.rule_id)}">'
        )
        lines.append(
            f'    <failure message="{escape(finding.message)}">{escape(finding.path)}</failure>'
        )
        lines.append("  </testcase>")
    lines.append("</testsuite>")
    return "\n".join(lines)
