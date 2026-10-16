"""Versioned caller review records using the existing atomic/persistent write wrapper."""

from __future__ import annotations

import copy
from typing import Callable

from api.ai import desk_review
from api.location.google_maps import ReviewLocation, maps_url
from api.rules.preparation import compact_preparation_notes
from api.server.memory import NotFound, Refused


def callers(memory, database) -> list[dict]:
    return database.callers() if database else list(memory.store.seed.get("callers", {}).values())


def caller(memory, database, report_id: str) -> dict:
    row = next((r for r in callers(memory, database) if r["report_id"] == report_id), None)
    if row is None:
        raise NotFound(report_id)
    return row


def approval_time(memory, database, report_id: str) -> str | None:
    """Read current approval under the caller's records lock, checking canonical input."""
    review = memory.store.seed.get("callerReviews", {}).get(report_id)
    if not review or not review.get("approved") or review.get("checked_by") != "Human":
        return None
    row = next((r for r in callers(memory, database) if r["report_id"] == report_id), None)
    if row and review.get("input_revision") == desk_review.input_revision(row):
        return review.get("approved_at")
    return None


def view(memory, database) -> dict:
    with memory.lock:
        reports = {r["reportId"]: r for r in memory.store.seed.get("reports", [])}
        reviews = memory.store.seed.get("callerReviews", {})
        history = memory.store.seed.get("callerReviewHistory", {})
        rows = []
        for c in callers(memory, database):
            rid = c["report_id"]
            r = reports.get(rid, {})
            revision = desk_review.input_revision(c)
            review = copy.deepcopy(reviews.get(rid))
            if review:
                review["volunteer_summary"] = compact_preparation_notes(review.get("volunteer_summary"))
            stale = bool(review and review["input_revision"] != revision)
            floor = desk_review.safety_evidence(c) if not review or stale else []
            floor_level = "1a" if any(e.kind == "medical_emergency" for e in floor) else "1b" if floor else None
            if stale:
                review.update(checked_by=None, review_status="human_review_required", approved=False, approved_by=None, approved_at=None)
                if floor_level:
                    review.update(emergency_level=floor_level, immediate_danger=True)
            rows.append({**c, "received_at": r.get("receivedAt"), "report_status": r.get("status", "reported"),
                         "input_revision": revision, "review": review, "review_stale": stale,
                         "immediate_danger": bool(floor or (review or {}).get("immediate_danger")),
                         "reported_emergency_level": floor_level,
                         "history": copy.deepcopy(history.get(rid, []))})
        rows.sort(key=desk_review.sort_key)
        return {"generated_at": memory.clock.iso(), "callers": rows,
                "counts": {"total": len(rows),
                           "ai_read": sum((r["review"] or {}).get("checked_by") == "AI" for r in rows),
                           "human_reviewed": sum((r["review"] or {}).get("checked_by") == "Human" for r in rows),
                           "needs_review": sum(not (r["review"] or {}).get("approved", False) for r in rows)}}


def _save(memory, report_id: str, review: dict) -> dict:
    reviews = memory.store.seed.setdefault("callerReviews", {})
    review = {**review, "review_revision": reviews.get(report_id, {}).get("review_revision", 0) + 1,
              "reviewed_at": memory.clock.iso()}
    reviews[report_id] = review
    memory.store.seed.setdefault("callerReviewHistory", {}).setdefault(report_id, []).append(copy.deepcopy(review))
    return review


def ai_review(memory, database, report_id: str, use_model: bool, submission_id: str | None = None,
              is_current: Callable[[], bool] = lambda: True) -> dict:
    with memory.lock:
        if submission_id and submission_id in memory.done:
            return copy.deepcopy(memory.done[submission_id]["value"])
        c = copy.deepcopy(caller(memory, database, report_id))
        previous = memory.store.seed.get("callerReviews", {}).get(report_id)
        if previous and previous.get("checked_by") == "Human" and previous["input_revision"] == desk_review.input_revision(c):
            return copy.deepcopy(previous)
        expected = previous.get("review_revision", 0) if previous else 0
    review = desk_review.generate(c, use_model)  # Network work never holds the records lock.

    def save():
        if not is_current():
            raise Refused("VERSION_CONFLICT", "The demo was reset during review. Refresh the caller list.")
        latest = memory.store.seed.get("callerReviews", {}).get(report_id)
        if desk_review.input_revision(caller(memory, database, report_id)) != review["input_revision"]:
            raise Refused("VERSION_CONFLICT", "Caller information changed. Review the latest record.")
        if latest and latest["review_revision"] != expected:
            return latest  # Another AI/human review won; never overwrite it with an older result.
        return _save(memory, report_id, {**review, "reviewed_by": None})

    return memory.write(submission_id, save)["value"]


def human_review(memory, database, report_id: str, data: dict) -> dict:
    c = caller(memory, database, report_id)
    previous = memory.store.seed.get("callerReviews", {}).get(report_id)
    revision = desk_review.input_revision(c)
    if revision != data["input_revision"] or (previous or {}).get("review_revision", 0) != data["expected_revision"]:
        raise Refused("VERSION_CONFLICT", "The caller or review changed. Refresh before saving.")
    if not data["reason"].strip() or not data["reviewed_by"].strip():
        raise Refused("INVALID", "Record who reviewed this case and why.")
    if data["immediate_danger"] and data["emergency_level"] is not None and data["emergency_level"] not in ("1a", "1b"):
        raise Refused("INVALID", "Immediate danger must remain an emergency level (1a or 1b).")
    transport = data.get("transport_recommendation") or "needs_assessment"
    previous_location = (previous or {}).get("resolved_location") or {}
    location = data.get("resolved_location") or previous_location
    location = ReviewLocation.model_validate(location).model_dump()
    location["address"] = (location["address"] or "").strip() or None
    has_point = location["latitude"] is not None and location["longitude"] is not None
    location["status"] = "resolved" if location["address"] and has_point else "partial" if location["address"] or has_point else "unresolved"
    changed_location = any(location[k] != previous_location.get(k) for k in ("address", "latitude", "longitude"))
    location["source"] = "human" if changed_location else previous_location.get("source", "unresolved")
    location["map_url"] = c.get("location") if maps_url(c.get("location") or "") else None
    approved = bool(data.get("approve"))
    if approved and any(not (c.get(field) or "").strip() for field in ("phone_number", "type", "location")):
        raise Refused("INCOMPLETE_REVIEW", "Phone number, help type and submitted location are required for approval.")
    result = {**(previous or {}), "transport_recommendation": transport,
              "emergency_level": data["emergency_level"], "immediate_danger": data["immediate_danger"],
              "volunteer_summary": (data["volunteer_summary"].strip() or None) if data["volunteer_summary"] is not None else None,
              "checked_by": "Human", "reviewed_by": data["reviewed_by"].strip(), "source": "human",
              "resolved_location": location, "approved": approved,
              "approved_by": data["reviewed_by"].strip() if approved else None,
              "approved_at": memory.clock.iso() if approved else None,
              "review_status": "human_reviewed" if approved or (data["emergency_level"] and transport != "needs_assessment") else "human_review_required",
              "clinical_assessment": "not_assessed", "input_revision": revision,
              "rules_version": desk_review.RULES_VERSION, "reasons": [data["reason"].strip()],
              "evidence": (previous or {}).get("evidence", []),
              "missing_information": (["Confirm current urgency."] if data["emergency_level"] is None else []) +
                                     (["Confirm suitable access and rescue capability."] if transport == "needs_assessment" else [])}
    return _save(memory, report_id, result)
