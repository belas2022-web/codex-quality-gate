from __future__ import annotations

import os


def get_env_name(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return None
    return value


def require_env_name(name: str) -> str:
    value = get_env_name(name)
    if value is None:
        raise ValueError(f"Required environment variable is not set: {name}")
    return value
