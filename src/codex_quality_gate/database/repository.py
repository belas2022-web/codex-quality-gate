from __future__ import annotations

import json
import sqlite3
from typing import Any

from codex_quality_gate.chat_bridge.sanitizer import redact_nested
from codex_quality_gate.core.result import Finding


class Repository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create_scan_run(self, project: str) -> int:
        cursor = self.connection.execute("INSERT INTO scan_runs(project) VALUES (?)", (project,))
        self.connection.commit()
        if cursor.lastrowid is None:
            raise RuntimeError("SQLite did not return a scan run id")
        return cursor.lastrowid

    def save_finding(self, run_id: int, finding: Finding) -> None:
        self.connection.execute(
            "INSERT INTO findings(run_id, rule_id, path, severity, message) VALUES (?, ?, ?, ?, ?)",
            (run_id, finding.rule_id, finding.path, finding.severity.value, finding.message),
        )
        self.connection.commit()

    def save_update_history(self, version: str, status: str) -> None:
        self.connection.execute(
            "INSERT INTO update_history(version, status) VALUES (?, ?)",
            (version, status),
        )
        self.connection.commit()

    def save_audit_event(self, event_type: str, payload: dict[str, object]) -> None:
        redacted_payload = _redact_payload(payload)
        self.connection.execute(
            "INSERT INTO audit_events(event_type, payload) VALUES (?, ?)",
            (event_type, json.dumps(redacted_payload, sort_keys=True)),
        )
        self.connection.commit()

    def save_policy_violation(self, policy: str, reason: str) -> None:
        self.connection.execute(
            "INSERT INTO policy_violations(policy, reason) VALUES (?, ?)",
            (policy, reason),
        )
        self.connection.commit()

    def summary(self) -> dict[str, object]:
        projects = self.connection.execute(
            "SELECT COUNT(DISTINCT project) FROM scan_runs"
        ).fetchone()[0]
        runs = self.connection.execute("SELECT COUNT(*) FROM scan_runs").fetchone()[0]
        findings = self.connection.execute("SELECT COUNT(*) FROM findings").fetchone()[0]
        critical = self.connection.execute(
            "SELECT COUNT(*) FROM findings WHERE severity = 'critical'"
        ).fetchone()[0]
        updates = self.connection.execute("SELECT COUNT(*) FROM update_history").fetchone()[0]
        return {
            "projects": int(projects),
            "runs": int(runs),
            "findings": int(findings),
            "critical_findings": int(critical),
            "updates": int(updates),
            "mode": "observe",
        }

    def list_projects(self) -> list[dict[str, object]]:
        rows = self.connection.execute(
            """
            SELECT project, COUNT(*) AS runs, MAX(id) AS latest_run_id, MAX(created_at) AS last_scan
            FROM scan_runs
            GROUP BY project
            ORDER BY project
            """
        ).fetchall()
        return [
            {
                "name": row[0],
                "runs": int(row[1]),
                "latest_run_id": int(row[2]),
                "last_scan": row[3],
            }
            for row in rows
        ]

    def list_findings(
        self,
        *,
        severity: str | None = None,
        project: str | None = None,
    ) -> list[dict[str, object]]:
        query = """
            SELECT findings.id, scan_runs.project, findings.run_id, findings.rule_id,
                   findings.path, findings.severity, findings.message
            FROM findings
            JOIN scan_runs ON scan_runs.id = findings.run_id
        """
        conditions: list[str] = []
        params: list[object] = []
        if severity:
            conditions.append("findings.severity = ?")
            params.append(severity)
        if project:
            conditions.append("scan_runs.project = ?")
            params.append(project)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY findings.id DESC"
        rows = self.connection.execute(query, params).fetchall()
        return [
            {
                "id": int(row[0]),
                "project": row[1],
                "run_id": int(row[2]),
                "rule_id": row[3],
                "path": row[4],
                "severity": row[5],
                "message": row[6],
            }
            for row in rows
        ]

    def list_runs(self, *, project: str | None = None) -> list[dict[str, object]]:
        if project:
            rows = self.connection.execute(
                "SELECT id, project, created_at FROM scan_runs WHERE project = ? ORDER BY id DESC",
                (project,),
            ).fetchall()
        else:
            rows = self.connection.execute(
                "SELECT id, project, created_at FROM scan_runs ORDER BY id DESC"
            ).fetchall()
        return [{"id": int(row[0]), "project": row[1], "created_at": row[2]} for row in rows]

    def list_update_history(self) -> list[dict[str, object]]:
        rows = self.connection.execute(
            "SELECT id, version, status FROM update_history ORDER BY id DESC"
        ).fetchall()
        return [{"id": int(row[0]), "version": row[1], "status": row[2]} for row in rows]

    def list_audit_events(self) -> list[dict[str, object]]:
        rows = self.connection.execute(
            "SELECT id, event_type, payload FROM audit_events ORDER BY id DESC"
        ).fetchall()
        events: list[dict[str, object]] = []
        for row in rows:
            events.append(
                {
                    "id": int(row[0]),
                    "event_type": row[1],
                    "payload": _decode_payload(row[2]),
                }
            )
        return events


def _decode_payload(payload: str) -> dict[str, Any]:
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError:
        return _redact_payload({"raw": payload})
    decoded_payload = decoded if isinstance(decoded, dict) else {"value": decoded}
    return _redact_payload(decoded_payload)


def _redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    redacted = redact_nested(payload)
    if not isinstance(redacted, dict):
        return {}
    return redacted


def _redact_value(value: Any) -> Any:
    return redact_nested(value)


def sanitize_existing_audit_payloads(connection: sqlite3.Connection) -> int:
    rows = connection.execute("SELECT id, payload FROM audit_events").fetchall()
    updated = 0
    for row in rows:
        row_id = int(row[0])
        payload = str(row[1])
        redacted_payload = json.dumps(_decode_payload(payload), sort_keys=True)
        if redacted_payload == payload:
            continue
        connection.execute(
            "UPDATE audit_events SET payload = ? WHERE id = ?",
            (redacted_payload, row_id),
        )
        updated += 1
    if updated:
        connection.commit()
    return updated
