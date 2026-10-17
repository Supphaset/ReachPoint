"""Demo rooms: each visitor gets their own copy of the demo, so judges trying it at the same time never see or undo
each other's requests, approvals or the boat breakdown, and a reset only resets your room.

The browser sends its room in the `X-Demo-Room` header (web/src/data/room.ts); the phones on /demo share one room
because they share the browser's storage, and `?room=CODE` opens the same room on another device. No header means
the shared "main" room (tests, curl). A room is about 1 MB; the least recently used rooms are dropped past the cap.
This replaces sign-in for the demo only: there are no accounts, and every room holds synthetic data.
"""

from __future__ import annotations

import os
import re
import threading
import time
from collections import OrderedDict
from contextvars import ContextVar
from dataclasses import dataclass, field

from api.server.flood_replay import FloodReplay
from api.server.memory import Clock, MemoryStore

MAIN = "main"
MAX_ROOMS = int(os.environ.get("REACHPOINT_MAX_ROOMS", "200"))
VALID = re.compile(r"^[A-Za-z0-9-]{4,40}$")


@dataclass
class Room:
    id: str
    memory: MemoryStore
    flood_replay: FloodReplay
    triage_lock: threading.Lock = field(default_factory=threading.Lock)
    triage_again: threading.Event = field(default_factory=threading.Event)
    used: float = field(default_factory=time.monotonic)


def _new(room_id: str) -> Room:
    memory = MemoryStore(clock=Clock(os.environ.get("REACHPOINT_CLOCK", "demo")))
    return Room(room_id, memory, FloodReplay(memory.store.catalogue))


class Rooms:
    def __init__(self, cap: int = MAX_ROOMS):
        self.cap = cap
        self._rooms: OrderedDict[str, Room] = OrderedDict()
        self._lock = threading.Lock()
        self.current_id: ContextVar[str] = ContextVar("demo_room", default=MAIN)

    @staticmethod
    def clean(room_id: str | None) -> str:
        return room_id if room_id and VALID.match(room_id) else MAIN

    def get(self, room_id: str) -> Room:
        with self._lock:
            room = self._rooms.get(room_id)
            if room is None:
                room = self._rooms[room_id] = _new(room_id)
                while len(self._rooms) > self.cap:
                    oldest = next(k for k in self._rooms if k != MAIN)
                    del self._rooms[oldest]
            self._rooms.move_to_end(room_id)
            room.used = time.monotonic()
            return room

    def current(self) -> Room:
        return self.get(self.current_id.get())

    def reset(self, room_id: str) -> Room:
        from api.v2 import store
        store.delete(room_id)
        with self._lock:
            self._rooms[room_id] = room = _new(room_id)
            return room

    def all(self) -> list[Room]:
        with self._lock:
            return list(self._rooms.values())

    def __len__(self) -> int:
        return len(self._rooms)


class RoomAttr:
    """`memory` and `flood_replay` in api/main.py: whatever the current request's room holds."""

    def __init__(self, rooms: Rooms, attr: str):
        object.__setattr__(self, "_rooms", rooms)
        object.__setattr__(self, "_attr", attr)

    def __getattr__(self, name):
        return getattr(getattr(self._rooms.current(), self._attr), name)
