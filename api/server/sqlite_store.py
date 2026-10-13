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
            self._db.execute("CREATE TABLE IF NOT EXISTS state (name TEXT PRIMARY KEY, payload TEXT NOT NULL)")
            self._db.execute("""CREATE TABLE IF NOT EXISTS call_sessions
                                (id TEXT PRIMARY KEY, created_at REAL NOT NULL, payload TEXT NOT NULL)""")

    def get(self, name: str) -> dict | None:
        with self._lock:
            row = self._db.execute("SELECT payload FROM state WHERE name = ?", (name,)).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, name: str, value: dict) -> None:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        with self._lock, self._db:
            self._db.execute("INSERT INTO state(name, payload) VALUES (?, ?) "
                             "ON CONFLICT(name) DO UPDATE SET payload = excluded.payload", (name, payload))

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

    def persist(self) -> None:
        """Save a derived update while the caller holds self.lock."""
        self.database.put("operations", self._snapshot())

    def write(self, submission_id: str | None, fn: Callable[[], Any]) -> dict:
        with self.lock:
            if submission_id and submission_id in self.done:
                return self.done[submission_id]
            before, counter = copy.deepcopy(self.store.seed), self.counter
            try:
                result = {"ok": True, "value": fn()}
                if submission_id:
                    self.done[submission_id] = result
                self.persist()
            except Exception:
                self.store.seed, self.counter = before, counter
                if submission_id:
                    self.done.pop(submission_id, None)
                raise
            return result
