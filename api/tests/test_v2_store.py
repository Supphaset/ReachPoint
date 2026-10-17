"""Persistence uses synthetic rooms and a local Firestore stand-in, with no Google credentials."""

import copy
import json
import logging
import threading

import pytest

from api.server.rooms import Rooms
from api.v2 import routes as R, store as S
from api.v2.intake import Session, new_session
from api.v2.reader import Fact, Read


class FakeFirestore:
    def __init__(self):
        self.docs = {}
        self.written = threading.Event()
        self.deleted = threading.Event()

    def collection(self, name):
        assert name == "v2rooms"
        return self

    def document(self, room_id):
        client = self

        class Document:
            def set(self, data, **kwargs):
                client.docs[room_id] = copy.deepcopy(data)
                client.written.set()

            def get(self, **kwargs):
                data = copy.deepcopy(client.docs.get(room_id))

                class Snapshot:
                    exists = data is not None

                    def to_dict(self):
                        return data

                return Snapshot()

            def delete(self, **kwargs):
                client.docs.pop(room_id, None)
                client.deleted.set()

        return Document()


@pytest.fixture
def storage(monkeypatch):
    client = FakeFirestore()
    monkeypatch.setenv("RP_FIRESTORE", "1")
    monkeypatch.setattr(S, "_client", client)
    monkeypatch.setattr(S, "_pending", {})
    monkeypatch.setattr(S, "_deleted", set())
    monkeypatch.setattr(S, "_generation", {})
    monkeypatch.setattr(S, "_last_error", None)
    monkeypatch.setattr(S, "_last_warning", float("-inf"))
    monkeypatch.setattr(S, "DEBOUNCE_S", 0.05)
    registry = Rooms()
    registry.current_id.set("store-test")
    monkeypatch.setattr(R, "_rooms_ref", registry)
    yield client
    for timer in list(S._pending.values()):
        timer.cancel()
        timer.join(timeout=2)
    with S._io:
        pass


def test_room_round_trip_and_restart_after_real_routes(storage, monkeypatch):
    R.post_plan(R.PlanIn(text="Rescue boat, 6 seats, D7 around 10:00, evacuation", team="Test boat"))
    R.v_outcome("HH055", R.OutcomeIn(outcome="nobodyThere", team="Test boat"))
    R.v_first("HH055", R.FirstIn(team="Test boat"))
    session = R.new_chat(lang="en")
    reply = R.turn(session["id"], "Water at my waist, 2 people, mother cannot walk, house 52/9 Phetkasem Soi 2")
    R.session_ready(session["id"], R.ReadyIn(done=[0, 2]))
    R.clock(R.ClockIn(action="advance"))
    R.clock(R.ClockIn(action="rain"))
    R.clock(R.ClockIn(action="flood"))
    old = R.room()
    expected = R.v_case("HH055", team="Test boat")
    assert storage.written.wait(5)
    # Wait for any save that was already running when the final mutation arrived.
    timer = S._pending.get("store-test")
    if timer:
        timer.join(5)
    restored = S.load("store-test")
    assert restored["now_h"] == old.now_h
    assert restored["seq"] == old.seq
    assert restored["plans"] == old.plans
    assert restored["first"] == old.first
    assert restored["alerts"] == old.alerts and restored["pulled"] == old.pulled
    assert restored["sessions"][session["id"]].to_dict() == old.sessions[session["id"]].to_dict()
    assert any(isinstance(m.get("_read"), Read) for m in restored["messages"])
    assert "_cache" not in storage.docs["store-test"] and "lock" not in storage.docs["store-test"]
    # Seed messages are replayed, not duplicated into the document.
    assert len(json.loads(storage.docs["store-test"]["messages"])) == len(old.messages)
    registry = Rooms()
    registry.current_id.set("store-test")
    monkeypatch.setattr(R, "_rooms_ref", registry)
    new = R.room()
    assert new is not old
    assert R.v_case("HH055", team="Test boat")["household"]["outcome"] == expected["household"]["outcome"]
    assert new.first == old.first
    assert R.session_status(session["id"])["householdId"] == reply["session"]["householdId"]
    assert new.sessions[session["id"]].ready == [0, 2]


def test_session_keeps_followups_and_pending_neighbours():
    s = new_session("en")
    s.nb_queue = [{"nb": {"side": "north"}, "cands": ["b1", "b2"], "i": 1, "quote": "next door"}]
    s.shelter_nearest = {"name": "School", "nameEn": "School", "route": [[1, 2], [3, 4]]}
    s.follow, s.finished, s.ride_requested = "leaveAsk", True, True
    restored = Session.from_dict(s.to_dict())
    assert restored == s
    assert restored.token == s.token


def test_read_facts_survive_and_effect_caches_are_skipped(storage):
    v = R.room()
    v.messages = [{"id": "L1", "atH": 96, "text": "two", "_read": Read([Fact("people", 2, "two")]),
                   "_effects": {"not": "durable"}}]
    S.save("store-test", v)
    msg = S.load("store-test")["messages"][0]
    assert msg["_read"].get("people") == 2
    assert "_effects" not in msg


def test_save_is_debounced_and_never_waits_for_firestore(storage, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    original = S.save

    def slow_save(room_id, v):
        entered.set()
        assert release.wait(5)
        original(room_id, v)

    monkeypatch.setattr(S, "save", slow_save)
    v = R.room()
    for _ in range(5):
        R.clock(R.ClockIn(action="advance"))
    assert not entered.is_set()
    assert entered.wait(2)
    # Another request can still update the clock while Firestore is blocked.
    R.clock(R.ClockIn(action="advance"))
    release.set()
    assert storage.written.wait(2)
    assert v.now_h == 99


def test_reset_cancels_pending_save_and_deletes_document(storage):
    v = R.room()
    lock = v.lock
    S.save("store-test", v)
    R.post_plan(R.PlanIn(text="boat 6 seats D7"))
    R.clock(R.ClockIn(action="reset"))
    assert storage.deleted.wait(2)
    assert S.load("store-test") is None
    assert v.lock is lock
    assert not v.plans and not v.sessions and v.seq == 0
    assert "store-test" not in storage.docs


def test_reset_wins_over_a_save_in_flight(storage, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    original = storage.document

    def document(room_id):
        doc = original(room_id)
        write = doc.set

        def blocked(data, **kwargs):
            entered.set()
            assert release.wait(5)
            write(data, **kwargs)

        doc.set = blocked
        return doc

    monkeypatch.setattr(storage, "document", document)
    R.clock(R.ClockIn(action="advance"))
    assert entered.wait(2)
    R.clock(R.ClockIn(action="reset"))
    assert S.load("store-test") is None
    release.set()
    assert storage.deleted.wait(2)
    assert "store-test" not in storage.docs


def test_size_limit_drops_oldest_messages_without_changing_live_room(storage, caplog):
    v = R.room()
    v.messages = [{"id": f"L{i}", "text": "น้ำ" * 10000} for i in range(15)]
    with caplog.at_level(logging.WARNING):
        S.save("store-test", v)
    data = storage.docs["store-test"]
    assert S._size(data) < 900_000
    kept = S.load("store-test")["messages"]
    assert 0 < len(kept) < len(v.messages)
    assert kept[-1]["id"] == "L14" and kept[0]["id"] != "L0"
    assert len(v.messages) == 15
    assert "dropped oldest live messages" in caplog.text


def test_unshrinkable_room_is_not_written(storage):
    v = R.room()
    v.plans = [{"text": "x" * 900_000}]
    S.save("store-test", v)
    assert not storage.docs
    assert S.status()["lastSaveError"] == "ValueError"


def test_errors_are_redacted_throttled_and_reported(storage, monkeypatch, caplog):
    def fail():
        raise RuntimeError("private words must never be logged")

    monkeypatch.setattr(S, "_db", fail)
    with caplog.at_level(logging.WARNING):
        S.save("store-test", R.room())
        S.save("store-test", R.room())
        assert S.load("store-test") is None
    assert len(caplog.records) == 1
    assert "private words" not in caplog.text
    assert R.health() == {"ok": True, "store": "firestore", "lastSaveError": "RuntimeError"}
    monkeypatch.setattr(S, "_db", lambda: storage)
    S.save("store-test", R.room())
    assert S.status()["lastSaveError"] is None


def test_memory_mode_never_contacts_firestore(storage, monkeypatch):
    monkeypatch.delenv("RP_FIRESTORE")
    S.save("store-test", R.V2Room())
    S.delete("store-test")
    assert S.load("store-test") is None
    assert not storage.docs and not S._pending
    assert R.health()["store"] == "memory"


def test_english_case_messages_keep_the_original_family_words(storage):
    thai = R.v_case("HH055")
    english = R.v_case("HH055", lang="en")
    assert english["contact"]["sent"]
    assert all(o.get("en") and o["text"] == o["en"] for o in english["contact"]["sent"])
    assert english["story"] == thai["story"]
    assert all(o.get("en") for o in R._state(R.room())["world"].outbound)


def test_legacy_registry_reset_deletes_v2_storage(storage):
    S.save("store-test", R.room())
    R._rooms_ref.reset("store-test")
    assert S.load("store-test") is None
    assert storage.deleted.wait(2)
    assert not storage.docs


def test_new_changes_after_reset_are_durable(storage):
    R.clock(R.ClockIn(action="reset"))
    R.clock(R.ClockIn(action="advance"))
    assert storage.written.wait(2)
    assert S.load("store-test")["now_h"] == R.DEFAULT_NOW_H + 0.5
