from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from codex_quality_gate.core.result import Finding, Severity
from codex_quality_gate.dashboard.app import check_config, create_app
from codex_quality_gate.dashboard.schemas import DashboardConfig
from codex_quality_gate.database.repository import Repository
from codex_quality_gate.database.sqlite import connect


def test_health_endpoint() -> None:
    client = TestClient(create_app())
    assert client.get("/health").json()["status"] == "ok"


def test_summary_endpoint(tmp_path: Path) -> None:
    client = _seeded_client(tmp_path / "dashboard.sqlite")
    assert client.get("/summary").json()["projects"] == 1


def test_projects_endpoint(tmp_path: Path) -> None:
    client = _seeded_client(tmp_path / "dashboard.sqlite")
    assert client.get("/projects").json()[0]["name"] == "demo"


def test_create_project_endpoint() -> None:
    assert TestClient(create_app()).post("/projects", json={"name": "x"}).json()["accepted"]


def test_scan_project_endpoint() -> None:
    assert TestClient(create_app()).post("/projects/demo/scan").json()["status"] == "queued"


def test_findings_endpoint_filters(tmp_path: Path) -> None:
    client = _seeded_client(tmp_path / "dashboard.sqlite")
    findings = client.get("/findings?severity=error").json()
    assert findings[0]["rule_id"] == "SEC-PY-EVAL"


def test_runs_endpoint(tmp_path: Path) -> None:
    client = _seeded_client(tmp_path / "dashboard.sqlite")
    assert client.get("/runs").json()[0]["project"] == "demo"


def test_updates_endpoint(tmp_path: Path) -> None:
    client = _seeded_client(tmp_path / "dashboard.sqlite")
    response = client.get("/updates").json()
    assert response["signature"] == "required"
    assert response["history"][0]["version"] == "1.0.0"


def test_sources_endpoint() -> None:
    assert TestClient(create_app()).get("/sources").status_code == 200


def test_audit_endpoint(tmp_path: Path) -> None:
    client = _seeded_client(tmp_path / "dashboard.sqlite")
    assert client.get("/audit").json()[0]["event_type"] == "seed"


def test_dashboard_auth_required_when_public_host() -> None:
    public_host = "192.0.2.1"
    assert not check_config(public_host)["ok"]
    with pytest.raises(ValueError):
        create_app(DashboardConfig(host=public_host))


def _seeded_client(path: Path) -> TestClient:
    if path.exists():
        path.unlink()
    repo = Repository(connect(path))
    run_id = repo.create_scan_run("demo")
    repo.save_finding(
        run_id,
        Finding("f1", "demo.py", 1, 1, Severity.ERROR, "bad", "SEC-PY-EVAL", "security"),
    )
    repo.save_update_history("1.0.0", "verified")
    repo.save_audit_event("seed", {"ok": True})
    return TestClient(create_app(DashboardConfig(database_path=path)))
