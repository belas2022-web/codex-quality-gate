from __future__ import annotations

import json

from codex_quality_gate.core.result import ScanResult


def render_json(result: ScanResult) -> str:
    return json.dumps(result.to_dict(), indent=2, sort_keys=True)
