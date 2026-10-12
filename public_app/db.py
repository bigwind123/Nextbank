from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    native_team_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runtime_settings (
    name TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approvals (
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    model_id TEXT NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    state TEXT NOT NULL CHECK (state = 'approved'),
    created_at TEXT NOT NULL,
    PRIMARY KEY (workspace_id, model_id)
);
CREATE TABLE IF NOT EXISTS workspace_selections (
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    model_id TEXT NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    operation_id TEXT NOT NULL,
    selected_at TEXT NOT NULL,
    PRIMARY KEY (workspace_id, model_id)
);
CREATE TABLE IF NOT EXISTS registry_selection_receipts (
    operation_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS gateway_operations (
    id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    model_id TEXT NOT NULL REFERENCES models(id),
    actor_id TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('pending', 'unknown', 'selected')),
    provider_mode TEXT NOT NULL,
    provider_id TEXT NOT NULL DEFAULT '',
    error_code TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS gateway_operations_created_idx ON gateway_operations(created_at DESC);
"""


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10, isolation_level="DEFERRED")
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        try:
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            connection.execute(
                "INSERT OR IGNORE INTO workspaces(id, name, native_team_id, created_at) VALUES(?,?,?,?)",
                ("workspace-local-demo", "Local Demo Workspace", "", created_at),
            )
            connection.execute(
                "INSERT OR IGNORE INTO models(id, name, created_at) VALUES(?,?,?)",
                ("model-synthetic-chat", "sample-language-model", created_at),
            )
