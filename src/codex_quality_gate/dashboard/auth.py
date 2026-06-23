from __future__ import annotations

import hmac

from fastapi import Request

from codex_quality_gate.policies.access_policy import is_localhost

TOKEN_HEADER = "x-codex-quality-gate-token"  # noqa: S105
BEARER_PREFIX = "bearer "


def auth_required(host: str, token: str | None) -> bool:
    return not is_localhost(host) and token is None


def request_has_valid_token(request: Request, expected_token: str) -> bool:
    candidate = _token_from_authorization(request.headers.get("authorization"))
    if candidate is None:
        candidate = request.headers.get(TOKEN_HEADER)
    if candidate is None:
        return False
    return hmac.compare_digest(candidate, expected_token)


def _token_from_authorization(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized.lower().startswith(BEARER_PREFIX):
        return None
    token = normalized[len(BEARER_PREFIX) :].strip()
    return token or None
