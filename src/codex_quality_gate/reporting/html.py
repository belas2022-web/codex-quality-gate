from __future__ import annotations

from html import escape

from codex_quality_gate.core.result import ScanResult


def render_html(result: ScanResult) -> str:
    rows = "".join(
        f"<tr><td>{escape(finding.severity.value)}</td><td>{escape(finding.rule_id)}</td>"
        f"<td>{escape(finding.path)}:{finding.line}</td><td>{escape(finding.message)}</td></tr>"
        for finding in result.findings
    )
    return (
        "<!doctype html><html><head><title>codex-quality-gate</title></head>"
        f"<body><h1>{escape(result.project)}</h1><table>{rows}</table></body></html>"
    )
