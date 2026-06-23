from __future__ import annotations

from sqlite3 import Connection

from codex_quality_gate.database.sqlite import SCHEMA


def apply_migrations(connection: Connection) -> None:
    connection.executescript(SCHEMA)
