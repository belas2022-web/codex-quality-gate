from __future__ import annotations

from pathlib import Path

import pytest

from codex_quality_gate.core.errors import SecurityVerificationError
from codex_quality_gate.updates.security import safe_join, validate_update_url


def test_rejects_untrusted_redirect() -> None:
    with pytest.raises(SecurityVerificationError):
        validate_update_url("https://evil.example/rules.json", ["good.example"])


def test_offline_local_rules_path_stays_inside_cache(tmp_path: Path) -> None:
    rules_path = safe_join(tmp_path, "rules/default_rules.json")
    assert rules_path == tmp_path / "rules" / "default_rules.json"
