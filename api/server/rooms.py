"""Synthetic v2 demo rooms, with active-room leases and persistence before eviction.

X-Demo-Room or ?room=CODE selects a visitor's room; no header selects main.
"""

from __future__ import annotations

import os
import re
import threading
import time
from collections import OrderedDict
from contextvars import ContextVar
from dataclasses import dataclass, field

MAIN = "main"
MAX_ROOMS = int(os.environ.get("REACHPOINT_MAX_ROOMS", "300"))
VALID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


@dataclass
class Room:
    id: str
    active: int = 0
    used: float = field(default_factory=time.monotonic)


class Rooms:
    def __init__(self, cap: int = MAX_ROOMS):
        self.cap = cap
        self._rooms: OrderedDict[str, Room] = OrderedDict()
        self._lock = threading.RLock()
        self.current_id: ContextVar[str] = ContextVar("demo_room", default=MAIN)

    @staticmethod
    def clean(room_id: str | None) -> str:
        return room_id if room_id and VALID.match(room_id) else MAIN

    def get(self, room_id: str) -> Room:
        with self._lock:
            room = self._rooms.get(room_id)
            if room is None:
                if len(self._rooms) >= self.cap:
                    from api.v2 import store
                    from api.v2.limits import limited
                    oldest = next((k for k, r in self._rooms.items() if not r.active), None)
                    if oldest is None:
                        raise limited(5)
                    old = self._rooms[oldest]
                    if hasattr(old, "v2") and not store.flush(oldest, old.v2):
                        raise limited(5)
                    del self._rooms[oldest]
                room = self._rooms[room_id] = Room(room_id)
            self._rooms.move_to_end(room_id)
            room.used = time.monotonic()
            return room

    def contains(self, room_id):
        with self._lock:
            return room_id in self._rooms

    def acquire(self, room_id):
        with self._lock:
            room = self.get(room_id)
            room.active += 1
            return room

    def release(self, room):
        with self._lock:
            room.active -= 1

    def current(self) -> Room:
        return self.get(self.current_id.get())

    def all(self) -> list[Room]:
        with self._lock:
            return list(self._rooms.values())

    def __len__(self) -> int:
        return len(self._rooms)
