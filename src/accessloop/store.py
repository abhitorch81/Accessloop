"""Durable run snapshots and an append-only event log."""
import json
import sqlite3
from pathlib import Path
from typing import Any


class SQLiteStore:
    def __init__(self, path: str | Path):
        self.path = str(path)
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, messages TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, run_id TEXT NOT NULL, payload TEXT NOT NULL)")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def save(self, run_id: str, messages: list[dict[str, Any]], event: dict[str, Any]) -> None:
        with self._connect() as db:
            db.execute("INSERT INTO runs (id, messages) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET messages=excluded.messages", (run_id, json.dumps(messages)))
            db.execute("INSERT INTO events (run_id, payload) VALUES (?, ?)", (run_id, json.dumps(event)))

    def load(self, run_id: str) -> list[dict[str, Any]]:
        with self._connect() as db:
            row = db.execute("SELECT messages FROM runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(run_id)
        return json.loads(row[0])

    def events(self, run_id: str) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("SELECT payload FROM events WHERE run_id=? ORDER BY id", (run_id,)).fetchall()
        return [json.loads(row[0]) for row in rows]
