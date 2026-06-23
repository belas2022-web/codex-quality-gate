from __future__ import annotations

import json

from codex_quality_gate.core.result import ScanResult


def render_sarif(result: ScanResult) -> str:
    payload = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {"driver": {"name": "codex-quality-gate", "rules": []}},
                "results": [
                    {
                        "ruleId": finding.rule_id,
                        "level": "error"
                        if finding.severity.value in {"error", "critical"}
                        else "warning",
                        "message": {"text": finding.message},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": finding.path},
                                    "region": {
                                        "startLine": finding.line,
                                        "startColumn": finding.column,
                                    },
                                }
                            }
                        ],
                    }
                    for finding in result.findings
                ],
            }
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)
