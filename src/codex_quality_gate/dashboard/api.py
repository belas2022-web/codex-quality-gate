from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Request

from codex_quality_gate.chat_bridge.sanitizer import sanitize_api_response
from codex_quality_gate.database.repository import Repository

router = APIRouter()


def repository_from_request(request: Request) -> Repository:
    repository = getattr(request.app.state, "repository", None)
    if not isinstance(repository, Repository):
        raise TypeError("Dashboard repository is not configured")
    return repository


RepositoryDep = Annotated[Repository, repository_from_request]


@router.get("/health")
def health() -> dict[str, str]:
    return sanitize_api_response({"status": "ok"})


@router.get("/summary")
def summary(request: Request) -> dict[str, object]:
    return sanitize_api_response(repository_from_request(request).summary())


@router.get("/projects")
def projects(request: Request) -> list[dict[str, object]]:
    return sanitize_api_response(repository_from_request(request).list_projects())


@router.post("/projects")
def create_project(payload: dict[str, object], request: Request) -> dict[str, object]:
    repo = repository_from_request(request)
    name = str(payload.get("name") or "").strip()
    if name:
        run_id = repo.create_scan_run(name)
        repo.save_audit_event("dashboard.project.create", {"project": name, "run_id": run_id})
    else:
        repo.save_audit_event("dashboard.project.create.rejected", {"reason": "missing name"})
    return sanitize_api_response({"accepted": bool(name), "project": payload})


@router.post("/projects/{name}/scan")
def scan_project(name: str, request: Request) -> dict[str, str]:
    repo = repository_from_request(request)
    run_id = repo.create_scan_run(name)
    repo.save_audit_event("dashboard.project.scan", {"project": name, "run_id": run_id})
    return sanitize_api_response({"project": name, "status": "queued"})


@router.get("/findings")
def findings(request: Request, severity: str | None = None) -> list[dict[str, object]]:
    return sanitize_api_response(repository_from_request(request).list_findings(severity=severity))


@router.get("/projects/{name}/findings")
def project_findings(
    name: str,
    request: Request,
    severity: str | None = None,
) -> list[dict[str, object]]:
    return sanitize_api_response(
        repository_from_request(request).list_findings(project=name, severity=severity)
    )


@router.get("/runs")
def runs(request: Request) -> list[dict[str, object]]:
    return sanitize_api_response(repository_from_request(request).list_runs())


@router.get("/projects/{name}/runs")
def project_runs(name: str, request: Request) -> list[dict[str, object]]:
    return sanitize_api_response(repository_from_request(request).list_runs(project=name))


@router.get("/updates")
def updates(request: Request) -> dict[str, object]:
    return sanitize_api_response(
        {
            "rules": "local",
            "signature": "required",
            "history": repository_from_request(request).list_update_history(),
        }
    )


@router.get("/projects/{name}/updates")
def project_updates(name: str, request: Request) -> dict[str, object]:
    _ = name
    return updates(request)


@router.get("/sources")
def sources(request: Request) -> list[dict[str, object]]:
    config = config_from_request(request)
    updates = _dict_value(config.get("updates"))
    raw_sources = updates.get("sources", [])
    if not isinstance(raw_sources, list):
        return []
    return sanitize_api_response(
        [_source_status(item) for item in raw_sources if isinstance(item, dict)]
    )


@router.get("/chats")
def chats(request: Request) -> list[dict[str, object]]:
    config = config_from_request(request)
    chat_bridge = _dict_value(config.get("chat_bridge"))
    raw_connectors = chat_bridge.get("connectors", [])
    if not isinstance(raw_connectors, list):
        return []
    return sanitize_api_response(
        [_chat_status(item) for item in raw_connectors if isinstance(item, dict)]
    )


@router.get("/audit")
def audit(request: Request) -> list[dict[str, object]]:
    return sanitize_api_response(repository_from_request(request).list_audit_events())


def config_from_request(request: Request) -> dict[str, object]:
    payload = getattr(request.app.state, "config_payload", {})
    return payload if isinstance(payload, dict) else {}


def _source_status(item: dict[str, object]) -> dict[str, object]:
    last_error = item.get("last_error")
    return {
        "name": str(item.get("name", "")),
        "type": str(item.get("type", "")),
        "enabled": bool(item.get("enabled", False)),
        "status": str(item.get("status", "configured")),
        "last_sync_at": _optional_str(item.get("last_sync_at")),
        "last_error": str(last_error) if last_error is not None else None,
        "secrets_exposed": False,
    }


def _chat_status(item: dict[str, object]) -> dict[str, object]:
    last_error = item.get("last_error")
    allowed_read = _count_list(item.get("allowed_read_channels") or item.get("allowed_chat_ids"))
    allowed_write = _count_list(
        item.get("allowed_write_channels") or item.get("allowed_channel_ids")
    )
    return {
        "name": str(item.get("name", "")),
        "type": str(item.get("type", "")),
        "enabled": bool(item.get("enabled", False)),
        "status": str(item.get("status", "configured")),
        "last_sync_at": _optional_str(item.get("last_sync_at")),
        "last_error": str(last_error) if last_error is not None else None,
        "allowed_read_count": allowed_read,
        "allowed_write_count": allowed_write,
        "secrets_exposed": False,
    }


def _optional_str(value: object) -> str | None:
    return None if value is None else str(value)


def _count_list(value: object) -> int:
    return len(value) if isinstance(value, list) else 0


def _dict_value(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}
