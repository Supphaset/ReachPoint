"""Optional, single-process SQLite persistence for the local demo.

The existing rules still operate on one Store snapshot. SQLite saves that snapshot after
each accepted write, along with retry results. Firestore can later replace this adapter
without changing the routes or the rule methods.
"""

from __future__ import annotations

import copy
import json
import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from api.server.memory import Clock, MemoryStore
from api.intake.schema import HELP_REQUEST_FIELDS, HelpRequest


class SQLiteState:
    def __init__(self, path: str):
        file = Path(path).expanduser().resolve()
        file.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(file, os.O_CREAT | os.O_RDWR, 0o600)
        os.close(fd)
        file.chmod(0o600)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(file, check_same_thread=False, timeout=5)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=FULL")
        with self._db:
            self._db.execute("BEGIN")
            self._db.execute("CREATE TABLE IF NOT EXISTS state (name TEXT PRIMARY KEY, payload TEXT NOT NULL)")
            self._db.execute("""CREATE TABLE IF NOT EXISTS call_sessions
                                (id TEXT PRIMARY KEY, created_at REAL NOT NULL, payload TEXT NOT NULL)""")
            table_sql = """CREATE TABLE IF NOT EXISTS help_requests (
                                report_id TEXT PRIMARY KEY NOT NULL,
                                channel TEXT NOT NULL CHECK (channel IN ('chat', 'voice', 'form')),
                                phone_number TEXT,
                                type TEXT CHECK (type IN ('food', 'evacuation')),
                                people_details TEXT,
                                n_children INTEGER CHECK (n_children >= 0),
                                n_elders INTEGER CHECK (n_elders >= 0),
                                n_pets INTEGER CHECK (n_pets >= 0),
                                location TEXT,
                                coordinates TEXT,
                                location_details TEXT,
                                water_level TEXT,
                                situation_details TEXT,
                                emergency_detail TEXT,
                                other_details TEXT)"""
            existing = self._db.execute("SELECT sql FROM sqlite_master WHERE name = 'help_requests'").fetchone()
            existing_columns = {row[1] for row in self._db.execute("PRAGMA table_info(help_requests)")}
            if existing and (existing_columns != set(HELP_REQUEST_FIELDS) or "'form'" not in existing[0]):
                # Rebuild only this table; keep all retained values and request IDs.
                self._db.execute(table_sql.replace("help_requests (", "help_requests_updated ("))
                columns = ", ".join(HELP_REQUEST_FIELDS)
                retained = ", ".join(f'"{field}"' if field in existing_columns else "NULL" for field in HELP_REQUEST_FIELDS)
                self._db.execute(f"INSERT INTO help_requests_updated ({columns}) SELECT {retained} FROM help_requests")
                self._db.execute("DROP TABLE help_requests")
                self._db.execute("ALTER TABLE help_requests_updated RENAME TO help_requests")
            else:
                self._db.execute(table_sql)

    def get(self, name: str) -> dict | None:
        with self._lock:
            row = self._db.execute("SELECT payload FROM state WHERE name = ?", (name,)).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, name: str, value: dict) -> None:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        with self._lock, self._db:
            self._db.execute("INSERT INTO state(name, payload) VALUES (?, ?) "
                             "ON CONFLICT(name) DO UPDATE SET payload = excluded.payload", (name, payload))

    def put_operations(self, value: dict, help_request: dict | None = None) -> None:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        with self._lock, self._db:
            self._db.execute("INSERT INTO state(name, payload) VALUES ('operations', ?) "
                             "ON CONFLICT(name) DO UPDATE SET payload = excluded.payload", (payload,))
            if help_request:
                help_request = HelpRequest.model_validate(help_request).model_dump()
                placeholders = ", ".join("?" for _ in HELP_REQUEST_FIELDS)
                self._db.execute(f"INSERT INTO help_requests ({', '.join(HELP_REQUEST_FIELDS)}) "
                                 f"VALUES ({placeholders}) ON CONFLICT(report_id) DO NOTHING",
                                 tuple(help_request.get(field) for field in HELP_REQUEST_FIELDS))

    def put_help_request(self, value: dict) -> None:
        """Fill a row for a report saved by an earlier version of the local adapter."""
        with self._lock, self._db:
            # Historical rows without newly required fields remain readable and retryable.
            if self._db.execute("SELECT 1 FROM help_requests WHERE report_id = ?", (value.get("report_id"),)).fetchone():
                return
            value = HelpRequest.model_validate(value).model_dump()
            placeholders = ", ".join("?" for _ in HELP_REQUEST_FIELDS)
            self._db.execute(f"INSERT INTO help_requests ({', '.join(HELP_REQUEST_FIELDS)}) "
                             f"VALUES ({placeholders}) ON CONFLICT(report_id) DO NOTHING",
                             tuple(value.get(field) for field in HELP_REQUEST_FIELDS))

    def get_session(self, session_id: str) -> dict | None:
        with self._lock:
            row = self._db.execute("SELECT payload FROM call_sessions WHERE id = ?", (session_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def put_session(self, session_id: str, created_at: float, value: dict) -> None:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        with self._lock, self._db:
            self._db.execute("INSERT INTO call_sessions(id, created_at, payload) VALUES (?, ?, ?) "
                             "ON CONFLICT(id) DO UPDATE SET payload = excluded.payload",
                             (session_id, created_at, payload))

    def active_sessions(self, oldest: float) -> int:
        with self._lock, self._db:
            self._db.execute("DELETE FROM call_sessions WHERE created_at < ?", (oldest,))
            return self._db.execute("SELECT COUNT(*) FROM call_sessions").fetchone()[0]

    def delete_session(self, session_id: str) -> None:
        with self._lock, self._db:
            self._db.execute("DELETE FROM call_sessions WHERE id = ?", (session_id,))

    def clear(self) -> None:
        with self._lock, self._db:
            self._db.execute("DELETE FROM help_requests")
            self._db.execute("DELETE FROM call_sessions")
            self._db.execute("DELETE FROM state")


class SQLiteMemoryStore(MemoryStore):
    def __init__(self, database: SQLiteState, clock: Clock):
        saved = database.get("operations")
        if saved:
            saved_clock = saved["clock"]
            clock.mode = saved_clock["mode"]
            clock.start = datetime.fromisoformat(saved_clock["start"])
            clock.began = datetime.fromisoformat(saved_clock["began"])
        super().__init__(seed=saved["seed"] if saved else None, clock=clock)
        self.database = database
        if saved:
            self.done = saved["done"]
            self.counter = saved["counter"]

    def _snapshot(self) -> dict:
        return {"seed": self.store.seed, "done": self.done, "counter": self.counter,
                "clock": {"mode": self.clock.mode, "start": self.clock.start.isoformat(),
                          "began": self.clock.began.isoformat()}}

    def persist(self, help_request: dict | None = None) -> None:
        """Save a derived update while the caller holds self.lock."""
        self.database.put_operations(self._snapshot(), help_request)

    def write(self, submission_id: str | None, fn: Callable[[], Any], help_request: dict | None = None) -> dict:
        with self.lock:
            if submission_id and submission_id in self.done:
                return self.done[submission_id]
            before, counter = copy.deepcopy(self.store.seed), self.counter
            try:
                result = {"ok": True, "value": fn()}
                if submission_id:
                    self.done[submission_id] = result
                row = {**help_request, "report_id": result["value"]["reportId"]} if help_request else None
                self.persist(row)
            except Exception:
                self.store.seed, self.counter = before, counter
                if submission_id:
                    self.done.pop(submission_id, None)
                raise
            return result
