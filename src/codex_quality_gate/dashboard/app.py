from __future__ import annotations

import json
import sqlite3
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse, Response

from codex_quality_gate.dashboard.api import router
from codex_quality_gate.dashboard.auth import auth_required, request_has_valid_token
from codex_quality_gate.dashboard.schemas import DashboardConfig
from codex_quality_gate.database.repository import Repository
from codex_quality_gate.database.sqlite import SCHEMA, connect

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "data" / "default_config.json"


def create_app(config: DashboardConfig | None = None) -> FastAPI:
    cfg = config or DashboardConfig()
    if auth_required(cfg.host, cfg.auth_token):
        raise ValueError("Dashboard auth is required when host is not localhost")
    app = FastAPI(title="codex-quality-gate")
    auth_token = cfg.auth_token
    if auth_token is not None:

        @app.middleware("http")
        async def enforce_dashboard_auth(
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]],
        ) -> Response:
            if not request_has_valid_token(request, auth_token):
                return JSONResponse({"detail": "Unauthorized"}, status_code=401)
            return await call_next(request)

    if cfg.database_path is None:
        connection = sqlite3.connect(":memory:", check_same_thread=False)
        connection.executescript(SCHEMA)
    else:
        connection = connect(cfg.database_path)
    app.state.repository = Repository(connection)
    app.state.config_payload = load_config_payload(cfg.config_path)
    app.include_router(router)
    app.include_router(router, prefix="/api")
    return app


def check_config(host: str = "127.0.0.1", token: str | None = None) -> dict[str, object]:
    return {
        "host": host,
        "auth_required": auth_required(host, token),
        "ok": not auth_required(host, token),
    }


def load_config_payload(path: Path | None = None) -> dict[str, Any]:
    config_path = path or DEFAULT_CONFIG_PATH
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}
