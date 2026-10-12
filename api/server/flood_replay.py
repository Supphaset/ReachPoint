"""Isolated deterministic replay. It never writes operational reports/cases/allocations."""
from __future__ import annotations

import threading

from api.rules.replay import process
from api.server.memory import Refused
from data.surge import START, VERSION, generate


class FloodReplay:
    def __init__(self, catalogue):
        self.reports, _ = generate(catalogue)  # truth is discarded; never passed to process
        self.landmarks = {l["id"]: l for l in catalogue["landmarks"]}
        self.cursor = 0
        self.revision = 0
        self.processed = []
        self.done = {}
        self.lock = threading.Lock()

    def write(self, submission_id, expected_cursor, expected_revision, count=None):
        with self.lock:
            if submission_id in self.done:
                return self.done[submission_id]
            if self.cursor != expected_cursor or self.revision != expected_revision:
                raise Refused("VERSION_CONFLICT", "Replay changed in another tab; refresh before continuing")
            if count is None:
                next_cursor, results = 0, []
            else:
                next_cursor = min(len(self.reports), self.cursor + count)
                results = self.processed + [process(r, self.landmarks) for r in self.reports[self.cursor:next_cursor]]
            self.cursor, self.processed = next_cursor, results
            self.revision += 1
            response = {"ok": True, "cursor": self.cursor, "revision": self.revision, "total": len(self.reports)}
            self.done[submission_id] = response
            return response

    def snapshot(self):
        with self.lock:
            return {"version": VERSION, "revision": self.revision, "cursor": self.cursor, "total": len(self.reports),
                    "at": self.reports[self.cursor - 1]["receivedAt"] if self.cursor else START.isoformat().replace("+00:00", "Z"),
                    "records": list(self.processed), "mode": "deterministic_simulation"}
