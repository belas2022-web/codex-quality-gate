from __future__ import annotations


def is_localhost(host: str) -> bool:
    return host in {"127.0.0.1", "localhost", "::1"}
