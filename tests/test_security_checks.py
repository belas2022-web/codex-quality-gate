from __future__ import annotations

import pytest

from codex_quality_gate.core.errors import SecurityVerificationError
from codex_quality_gate.rules.rule_engine import RuleEngine
from codex_quality_gate.updates.security import validate_allowed_domain, validate_https_url


def test_rejects_http_update_url() -> None:
    with pytest.raises(SecurityVerificationError):
        validate_https_url("http://example.com/latest.json")


def test_rejects_untrusted_domain() -> None:
    with pytest.raises(SecurityVerificationError):
        validate_allowed_domain("https://evil.example/latest.json", ["good.example"])


def test_rejects_verify_false() -> None:
    assert RuleEngine().scan_text("x.py", "requests.get(url, verify=False, timeout=3)")


def test_detects_sql_fstring() -> None:
    assert RuleEngine().scan_text("x.py", 'query = f"select * from users where id={user_id}"')


def test_detects_innerhtml() -> None:
    assert RuleEngine().scan_text("x.js", "node.innerHTML = html")


def test_detects_dangerously_set_innerhtml() -> None:
    assert RuleEngine().scan_text("x.tsx", "<div dangerouslySetInnerHTML={x} />")


def test_detects_token_logging() -> None:
    assert RuleEngine().scan_text("x.py", "print(token)")
