"""The team and desk rules (C6, C7, D42) on an in-memory copy of the demo records. Owner: user (starter); the
friend replaces the storage with Firestore transactions and keeps these rules and results.

Each write is all-or-nothing under one lock (Firestore: one transaction over the listing, the team and its
resource). A repeated `submissionId` returns the first result and changes nothing. Rule failures raise `Refused`
with a code and a plain-English message, which the API turns into HTTP 409.
"""

from __future__ import annotations

import copy
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from api.views import store as views_store
from api.views.team import group_owner, seats, seats_used

ROOT = Path(__file__).resolve().parents[2]
DEMO_START = datetime(2026, 10, 11, 3, 16, tzinfo=timezone.utc)  # the web's demo clock starts at 10:16 Bangkok
OUTCOMES = ("done", "already_left", "not_found", "needs_more_help")


class Refused(Exception):
    def __init__(self, code: str, message: str, detail: dict | None = None):
        super().__init__(message)
        self.code, self.message, self.detail = code, message, detail or {}


class NotFound(KeyError):
    pass


class Clock:
    """Demo clock (default): starts at 10:16 on 11 Oct 2026 and runs in real time, like the web's clock.
    `real` uses the wall clock (for live data)."""

    def __init__(self, mode: str = "demo", start: datetime = DEMO_START):
        self.mode, self.start, self.began = mode, start, datetime.now(timezone.utc)

    def now(self) -> datetime:
        real = datetime.now(timezone.utc)
        return real if self.mode == "real" else self.start + (real - self.began)

    def iso(self) -> str:
        return self.now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _seats_text(n: float) -> str:
    return f"{n:g}" if float(n).is_integer() else f"{n:.1f}"


class MemoryStore:
    def __init__(self, seed: dict | None = None, clock: Clock | None = None, package: str = "hy-2025-11"):
        base = views_store.load(package)
        self.store = views_store.Store(copy.deepcopy(seed or base.seed), base.catalogue, base.exposure, base.register)
        self.store.seed.setdefault("allocations", [])
        self.clock = clock or Clock()
        self.lock = threading.Lock()
        self.done: dict[str, dict] = {}  # submissionId → first result
        self.counter = 0

    # --- lookups ---

    def _need(self, listing_id: str) -> tuple[dict, dict]:
        for c, n in self.store.needs():
            if n["listingId"] == listing_id:
                return c, n
        raise NotFound(listing_id)

    def _team(self, team_id: str) -> dict:
        t = self.store.team(team_id)
        if t is None:
            raise NotFound(team_id)
        return t

    def _alloc(self, allocation_id: str) -> dict:
        a = next((a for a in self.store.seed["allocations"] if a["allocationId"] == allocation_id), None)
        if a is None:
            raise NotFound(allocation_id)
        if a["state"] == "closed":
            raise Refused("ALLOCATION_CLOSED", "This job is closed", {"closedAt": a.get("closedAt"), "outcome": a.get("outcome")})
        return a

    def _summarise(self, need: dict) -> None:
        """Keep the need's summary (what the map and the zone order read) in line with its groups."""
        owners = [group_owner(self.store, need, f"{need['listingId']}-G{i + 1}") for i in range(len(need["groups"]))]
        if all(owners):
            teams = sorted(set(owners))
            need["allocation"] = {"state": "taken", **({"teamId": teams[0]} if len(teams) == 1 else {}), "fromAllocations": True}
        else:
            need["allocation"] = {"state": "open", "fromAllocations": True}

    # --- the write wrapper ---

    def write(self, submission_id: str | None, fn: Callable[[], Any]) -> dict:
        with self.lock:
            if submission_id and submission_id in self.done:
                return self.done[submission_id]
            before = copy.deepcopy(self.store.seed)
            try:
                result = {"ok": True, "value": fn()}
            except Exception:
                self.store.seed = before  # all or nothing
                raise
            if submission_id:
                self.done[submission_id] = result
            return result

    # --- team actions (C6) ---

    def claim(self, listing_id: str, team_id: str, group_ids: list[str], expected_revision: int) -> dict:
        case, need = self._need(listing_id)
        team = self._team(team_id)
        if team["status"] != "available":
            raise Refused("NOT_AVAILABLE", "Set your team to Available to take cases")
        if need["type"] not in team["capabilities"]:
            raise Refused("NOT_AVAILABLE", "Your team can't take this kind of case")
        if need["review"] != "validated":
            raise Refused("ALLOCATION_CLOSED", "This case is no longer open")
        if need["needRevision"] != expected_revision:
            raise Refused("NEED_CHANGED", "This case changed, please look again",
                          {"seenRevision": expected_revision, "currentRevision": need["needRevision"]})
        all_ids = [f"{listing_id}-G{i + 1}" for i in range(len(need["groups"]))]
        if not group_ids or any(g not in all_ids for g in group_ids):
            raise Refused("INVALID", "Pick at least one family group from this case")
        for g in group_ids:
            owner = group_owner(self.store, need, g)
            if owner:
                raise Refused("ALREADY_TAKEN", f"Already taken by {owner}", {"groupIds": [g], "takenBy": owner})
        want = sum(seats(need["groups"][all_ids.index(g)]["party"]) for g in group_ids)
        left = team["resource"]["seatUnits"] - seats_used(self.store, team_id)
        if want > left:
            raise Refused("NOT_ENOUGH_CAPACITY", f"Needs {_seats_text(want)} seats, you have {_seats_text(left)}",
                          {"seatsNeeded": want, "seatsLeft": left})
        self.counter += 1
        a = {"allocationId": f"AL-{listing_id[2:]}-{self.counter:03d}", "listingId": listing_id, "teamId": team_id,
             "resourceId": team["resource"]["resourceId"], "groupIds": list(group_ids), "seatUnits": want,
             "state": "taken", "window": None, "acceptedAt": self.clock.iso(), "needRevision": need["needRevision"]}
        self.store.seed["allocations"].append(a)
        self._summarise(need)
        return {"allocationId": a["allocationId"]}

    def set_window(self, allocation_id: str, start: str, end: str) -> None:
        a = self._alloc(allocation_id)
        if end <= start:
            raise Refused("INVALID", "The window must end after it starts")
        a["window"] = {"start": start, "end": end, "setAt": self.clock.iso()}

    def progress(self, allocation_id: str, state: str) -> None:
        if state not in ("on_the_way", "on_scene"):
            raise Refused("INVALID", "Progress is On the way or On scene")
        self._alloc(allocation_id)["state"] = state

    def close(self, allocation_id: str, outcome: str) -> None:
        if outcome not in OUTCOMES:
            raise Refused("INVALID", "Pick how the job ended")
        a = self._alloc(allocation_id)
        _, need = self._need(a["listingId"])
        a.update(state="closed", outcome=outcome, closedAt=self.clock.iso())
        if need.get("medicalNotes"):
            a["medicalRemovedAt"] = a["closedAt"]  # D38: notes leave the team's view when the job closes
        if outcome == "needs_more_help":
            self._reopen(need, a, "needs more help")
        self._summarise(need)

    def hand_back(self, allocation_id: str, reason: str) -> None:
        if not (reason or "").strip():
            raise Refused("INVALID", "Say why you're handing it back")
        a = self._alloc(allocation_id)
        _, need = self._need(a["listingId"])
        self._reopen(need, a, reason.strip())
        self.store.seed["allocations"].remove(a)
        self._summarise(need)

    def _reopen(self, need: dict, a: dict, why: str) -> None:
        need.setdefault("reasons", [])
        need["reasons"] = [r for r in need["reasons"] if not r.startswith("Back from")] + [f"Back from {a['teamId']}: {why}"]

    def team_status(self, team_id: str, status: str, reason: str | None, back_about: str | None) -> None:
        if status not in ("available", "busy", "off_duty"):
            raise Refused("INVALID", "Status is Available, Busy or Off duty")
        t = self._team(team_id)
        avail = status == "available"
        t.update(status=status, reason=None if avail else reason, backAbout=None if avail else back_about, statusSetAt=self.clock.iso())

    def reconfirm(self, listing_id: str, team_id: str | None) -> None:
        _, need = self._need(listing_id)
        need["reconfirmRequestedAt"] = self.clock.iso()

    # --- desk actions ---

    def urgent_flag(self, listing_id: str, reason: str, confirmed_now: bool) -> None:
        r = (reason or "").strip()
        if not r:
            raise Refused("INVALID", "An urgent flag needs a reason")
        case, need = self._need(listing_id)
        need["urgentFlag"] = {"reason": r}
        need["needRevision"] += 1
        if confirmed_now:
            case["lastConfirmedAt"] = self.clock.iso()

    def ask_teams(self, suggestion_id: str, team_ids: list[str]) -> dict:
        """C7 on the stored suggestion: the demo answer from askTeams.ok.json, or, for any other suggestion, one ask
        per team given. The friend's version writes one prompt to each team's view and returns VERSION_CONFLICT
        (`askTeams.stale.json` shape) when the suggestion's inputs changed."""
        ok = json.loads((ROOT / "contract" / "fixtures" / "askTeams.ok.json").read_text())
        if suggestion_id == ok["request"]["suggestionId"]:
            return ok["response"]
        return {"ok": True, "askedAt": self.clock.iso(), "note": "",
                "asks": [{"askId": f"ASK-{t}", "teamId": t, "listingIds": []} for t in team_ids]}
