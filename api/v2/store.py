"""Optional write-behind storage for synthetic v2 rooms. Cloud Run uses its own identity."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from contextlib import contextmanager

from api.v2.intake import Session
from api.v2.reader import Fact, Read

_client = None  # tests inject a Firestore-like client here
_pending = {}
_deleted = set()
_generation = {}
_guard = threading.Lock()
_io = threading.Lock()
_last_warning = float("-inf")
_last_error = None
DEBOUNCE_S = 1.5
MAX_BYTES = 900_000
FIELDS = ("now_h", "seq", "messages", "plans", "alerts", "pulled", "sessions", "first")


def enabled():
    return os.environ.get("RP_FIRESTORE") == "1"


def status():
    return {"store": "firestore" if enabled() else "memory", "lastSaveError": _last_error}


def _warning(error):
    global _last_warning
    with _guard:
        now = time.monotonic()
        if now - _last_warning >= 60:
            _last_warning = now
            logging.warning("v2 room store: %s", error)


def _failed(exc):
    global _last_error
    # Error text may contain credentials or household words; keep only its type.
    _last_error = type(exc).__name__
    _warning(_last_error)


def _db():
    global _client
    if _client is None:
        from google.cloud import firestore
        _client = firestore.Client(database="(default)")
    return _client


def _default(value):
    if isinstance(value, Read):
        return {"__read__": value.to_json()}
    raise TypeError(type(value).__name__)


def _object(value):
    if set(value) == {"__read__"}:
        r = value["__read__"]
        return Read([Fact(**f) for f in r["facts"]], reader=r["reader"])
    return value


def _encode(value):
    return json.dumps(value, default=_default, ensure_ascii=False, separators=(",", ":"))


def _snapshot(v):
    with v.lock:
        data = {k: getattr(v, k) for k in FIELDS}
        # The scenario is replayed by pipeline.run; messages holds only this room's additions.
        data["messages"] = [{k: val for k, val in m.items() if k != "_effects"} for m in v.messages]
        data["sessions"] = {k: s.to_dict() for k, s in v.sessions.items()}
        # JSON fields also support nested arrays, which Firestore values cannot represent directly.
        return {k: val if k in ("now_h", "seq") else _encode(val) for k, val in data.items()}


def _size(data):
    # Include ample room for the document name, field names and protobuf overhead.
    return sum(len(str(v).encode("utf-8")) + len(k) for k, v in data.items()) + 8192


def save(room_id, v):
    """Save a snapshot; callers use the background scheduler, never the request thread."""
    global _last_error
    if not enabled():
        return
    try:
        with _guard:
            generation = _generation.get(room_id, 0)
        data = _snapshot(v)
        messages = json.loads(data["messages"])
        dropped = 0
        while _size(data) >= MAX_BYTES and messages:
            messages.pop(0)
            dropped += 1
            data["messages"] = _encode(messages)
        if dropped:
            _warning("dropped oldest live messages to fit the document limit")
        if _size(data) >= MAX_BYTES:
            raise ValueError("room exceeds document limit without messages")
        _db().collection("v2rooms").document(room_id).set(data, timeout=10, retry=None)
        with _guard:
            if _generation.get(room_id, 0) == generation:
                _deleted.discard(room_id)
        _last_error = None
    except Exception as exc:
        _failed(exc)


def load(room_id):
    if not enabled():
        return None
    with _guard:
        if room_id in _deleted:
            return None
    try:
        doc = _db().collection("v2rooms").document(room_id).get(timeout=5, retry=None)
        if not doc.exists:
            return None
        data = {k: val if k in ("now_h", "seq") else json.loads(val, object_hook=_object)
                for k, val in doc.to_dict().items() if k in FIELDS}
        data["sessions"] = {k: Session.from_dict(s) for k, s in data.get("sessions", {}).items()}
        return data
    except Exception as exc:
        _failed(exc)
        return None


def _schedule(room_id, v=None):
    if not enabled():
        return

    def write():
        # Serialise writes and deletes so an older save cannot resurrect a reset room.
        with _io:
            with _guard:
                if _pending.get(room_id) is not timer:
                    return
                del _pending[room_id]
            if v is not None:
                save(room_id, v)
            else:
                try:
                    _db().collection("v2rooms").document(room_id).delete(timeout=10, retry=None)
                except Exception as exc:
                    _failed(exc)

    timer = threading.Timer(DEBOUNCE_S if v is not None else 0, write)
    timer.daemon = True
    with _guard:
        if v is None:
            _deleted.add(room_id)
            _generation[room_id] = _generation.get(room_id, 0) + 1
        old = _pending.pop(room_id, None)
        if old:
            old.cancel()
        _pending[room_id] = timer
    timer.start()


def schedule(v):
    if enabled():
        _schedule(v._room_id, v)


def delete(room_id):
    _schedule(room_id)


@contextmanager
def changing(v):
    with v.lock:
        try:
            yield
        finally:
            schedule(v)
