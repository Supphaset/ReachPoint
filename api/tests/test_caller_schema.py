"""Round-trip the same caller fields through form, chat, voice and legacy SQLite."""

import os
import copy
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

os.environ["REACHPOINT_AI"] = "off"

from fastapi.testclient import TestClient
from api import main
from api.intake import conversation
from api.intake.extract import extract
from api.intake.facts import FloodCase, next_question, render_summary
from api.intake.schema import HELP_REQUEST_FIELDS, HelpRequestDetails
from api.server.memory import Clock
from api.server.sqlite_store import SQLiteMemoryStore, SQLiteState

FIELDS = ("report_id", "channel", "phone_number", "type", "people_details", "n_children", "n_elders", "n_pets",
          "location", "coordinates", "location_details", "water_level", "situation_details",
          "emergency_detail", "other_details")
DETAILS = {
    "phone_number": "0000000000", "type": "food",
    "people_details": "Synthetic group of two adults and one child",
    "n_children": 1, "n_elders": 0, "n_pets": None,
    "location": "Synthetic building", "coordinates": "7.0, 100.5",
    "location_details": "Second floor", "water_level": "Knee height",
    "situation_details": "Need food", "emergency_detail": "No immediate danger", "other_details": None,
}


class CallerSchemaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = main.database, main.memory
        self.database = SQLiteState(str(Path(self.temp.name) / "callers.sqlite3"))
        main.database = self.database
        main.memory = SQLiteMemoryStore(self.database, Clock("demo"))
        conversation.configure_storage(self.database)
        self.client = TestClient(main.app)
        self.patches = [patch.object(main, "extract", side_effect=lambda text, *_: extract(text, use_model=False)),
                        patch.object(main, "resolve_location", return_value=None),
                        patch.object(main._triager, "submit")]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        main.database, main.memory = self.original
        conversation.configure_storage(main.database)
        self.database._db.close()
        self.temp.cleanup()

    def start(self):
        return self.client.post("/api/callers/sessions", json={}).json()

    def rows(self):
        self.database._db.row_factory = sqlite3.Row
        return [dict(row) for row in self.database._db.execute("SELECT * FROM help_requests")]

    def test_form_round_trip_preserves_fields_nulls_and_zero_and_retry(self):
        session = self.start()
        body = {**DETAILS, "phone_number": "000 000-0000", "submissionId": "form-once", "expectedRevision": 0}
        path = f"/api/callers/sessions/{session['sessionId']}/form"
        result = self.client.post(path, json=body)
        self.assertEqual(result.status_code, 200, result.text)
        value = result.json()
        self.assertTrue(value["sent"])
        row, = self.rows()
        self.assertEqual(tuple(row), FIELDS)
        self.assertEqual(row, {"report_id": value["sent"]["reportId"], "channel": "form", **DETAILS})
        self.assertEqual(self.client.post(path, json=body).json(), value)
        self.assertEqual(len(self.rows()), 1)
        self.assertEqual(self.client.get("/api" + value["sent"]["statusUrl"]).status_code, 200)
        conversation.clear_cache()
        resumed = self.client.get(f"/api/callers/sessions/{session['sessionId']}").json()
        self.assertEqual(resumed["sent"], value["sent"])
        self.assertNotIn("reporter_name", resumed["case"])

    def test_chat_and_voice_confirmation_use_same_fields(self):
        case = FloodCase(**DETAILS, unavailable_fields=["n_pets", "other_details"])
        with patch.object(main, "USE_AI", True), patch.object(conversation, "_extract", return_value=case), \
                patch.object(conversation, "_search", new=AsyncMock(return_value={"status": "unavailable"})):
            for channel in ("chat", "voice"):
                session = self.start()
                sid = session["sessionId"]
                if channel == "chat":
                    response = self.client.post(f"/api/callers/sessions/{sid}/turn", json={"text": "Synthetic request", "turnId": "one"})
                    self.assertEqual(response.status_code, 200, response.text)
                else:
                    # The Live tool calls this same turn function after transcribing audio.
                    import asyncio
                    asyncio.run(conversation.turn(conversation.get(sid), "Synthetic request", "one", channel="voice"))
                current = self.client.get(f"/api/callers/sessions/{sid}").json()
                self.assertTrue(current["canConfirm"])
                result = self.client.post(f"/api/callers/sessions/{sid}/confirm", json={"submissionId": channel, "expectedRevision": current["revision"]})
                self.assertEqual(result.status_code, 200, result.text)
                row = self.rows()[-1]
                self.assertEqual(row, {"report_id": result.json()["sent"]["reportId"], "channel": channel, **DETAILS})

    def test_invalid_form_does_not_save(self):
        session = self.start()
        base = {"phone_number": DETAILS["phone_number"], "type": "food", "submissionId": "bad", "expectedRevision": 0}
        for fields in ({"reporter_name": "Removed"}, {"n_children": -1}, {"n_children": 1.5},
                       {"coordinates": "not coordinates"}, {"coordinates": "100, 200"},
                       {"phone_number": None}, {"phone_number": ""}, {"phone_number": "123"},
                       {"phone_number": "letters0000000000"}, {"type": None}, {"type": "medical"}):
            result = self.client.post(f"/api/callers/sessions/{session['sessionId']}/form", json={**base, **fields})
            self.assertEqual(result.status_code, 422, result.text)
        self.assertEqual(self.rows(), [])
        for field in ("phone_number", "type"):
            missing = {key: value for key, value in base.items() if key != field}
            result = self.client.post(f"/api/callers/sessions/{session['sessionId']}/form", json=missing)
            self.assertEqual(result.status_code, 422)
        stale = self.client.post(f"/api/callers/sessions/{session['sessionId']}/form", json={**DETAILS, **base, "expectedRevision": 4})
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(self.rows(), [])

    def test_required_fields_cannot_be_skipped_in_chat_or_voice(self):
        for channel in ("chat", "voice"):
            for required in ("phone_number", "type"):
                session = conversation.get(self.start()["sessionId"])
                session.channel = channel
                session.messages.append({"role": "user", "text": "Synthetic urgent request"})
                session.case = FloodCase(**{**DETAILS, required: None}, immediate_danger=True,
                                         unavailable_fields=[required, "n_pets", "other_details"])
                self.assertFalse(session.ready())
                response = self.client.post(f"/api/callers/sessions/{session.id}/confirm",
                                            json={"submissionId": "missing", "expectedRevision": session.revision})
                self.assertEqual(response.status_code, 409)
        self.assertEqual(self.rows(), [])
        urgent = FloodCase(immediate_danger=True)
        self.assertIn("อยู่ที่ไหน", next_question(urgent))

    def test_receipt_answers_persist_and_do_not_change_volunteer_progress(self):
        session = self.start()
        result = self.client.post(f"/api/callers/sessions/{session['sessionId']}/form",
                                  json={**DETAILS, "submissionId": "receipt-request", "expectedRevision": 0}).json()
        sent = result["sent"]
        path = "/api" + sent["statusUrl"]
        before = copy.deepcopy(main.memory.store.seed["allocations"])
        initial = self.client.get(path).json()
        self.assertIsNone(initial["receipt"])
        self.assertTrue(initial["completedAt"][0])
        self.assertEqual(initial["completedAt"][1:], [None, None, None])
        no = self.client.post(path + "/receipt", json={"answer": "no", "submissionId": "no-once"})
        self.assertEqual(no.status_code, 200)
        self.assertIsNone(self.client.get(path).json()["completedAt"][3])
        yes = self.client.post(path + "/receipt", json={"answer": "yes", "submissionId": "yes-once"})
        self.assertEqual(yes.status_code, 200)
        self.assertEqual(self.client.post(path + "/receipt", json={"answer": "yes", "submissionId": "yes-once"}).json(), yes.json())
        self.assertEqual(len(main.memory.store.seed["receiptResponses"][sent["reportId"]]), 2)
        self.assertEqual(main.memory.store.seed["allocations"], before)
        main.memory = SQLiteMemoryStore(self.database, Clock("demo"))
        reloaded = self.client.get(path).json()
        self.assertEqual(reloaded["receipt"], yes.json())
        self.assertEqual(reloaded["completedAt"][3], yes.json()["at"])
        self.assertEqual(self.client.post("/api/status/missing/receipt", json={"answer": "yes", "submissionId": "yes-once"}).status_code, 404)
        self.assertEqual(self.client.post(path + "/receipt", json={"answer": "partial", "submissionId": "bad"}).status_code, 422)

    def test_completion_times_use_recorded_events_and_never_auto_confirm_receipt(self):
        session = self.start()
        result = self.client.post(f"/api/callers/sessions/{session['sessionId']}/form",
                                  json={**DETAILS, "submissionId": "timed-request", "expectedRevision": 0}).json()
        sent = result["sent"]
        report = next(row for row in main.memory.store.seed["reports"] if row["reportId"] == sent["reportId"])
        report["reviewedAt"] = "2026-10-11T03:20:00Z"
        main.memory.store.seed["statusTokens"][sent["statusToken"]]["caseId"] = "TIMED-CASE"
        main.memory.store.seed["cases"].append({"caseId": "TIMED-CASE", "lastConfirmedAt": report["reviewedAt"],
            "needs": [{"listingId": "TIMED-LISTING", "type": "evacuation_transport", "allocation": {"state": "open"},
                       "groups": [{"label": "Family 1"}]}]})
        main.memory.store.seed["allocations"].append({"listingId": "TIMED-LISTING", "groupIds": ["TIMED-LISTING-G1"],
            "state": "closed", "outcome": "done", "teamId": "T-S", "closedAt": "2026-10-11T03:40:00Z"})
        view = self.client.get("/api" + sent["statusUrl"]).json()
        self.assertEqual(view["completedAt"], [report["receivedAt"], report["reviewedAt"], "2026-10-11T03:40:00Z", None])
        self.assertEqual(view["lines"][0]["state"], "done")
        self.assertIsNone(view["receipt"])

    def test_names_removed_from_questions_summaries_and_case(self):
        case = FloodCase(reporter_name="Legacy value")
        self.assertNotIn("reporter_name", case.model_dump())
        self.assertNotIn("ชื่อผู้แจ้ง", next_question(case))
        self.assertNotIn("Legacy value", render_summary(case))
        self.assertEqual(tuple(HelpRequestDetails.model_fields), FIELDS[2:])
        self.assertEqual(HELP_REQUEST_FIELDS, FIELDS)

    def test_migration_keeps_retained_data_and_accepts_form(self):
        path = str(Path(self.temp.name) / "legacy.sqlite3")
        old = sqlite3.connect(path)
        legacy_fields = tuple(key for key in FIELDS[2:] if key not in ("phone_number", "type"))
        columns = ", ".join(f"{key} {'INTEGER' if key.startswith('n_') else 'TEXT'}" for key in legacy_fields)
        old.execute(f"CREATE TABLE help_requests (report_id TEXT PRIMARY KEY, channel TEXT CHECK(channel IN ('chat', 'voice')), reporter_name TEXT, {columns})")
        values = ("LEGACY-1", "voice", "Synthetic old name", *(DETAILS[key] for key in legacy_fields))
        old.execute(f"INSERT INTO help_requests VALUES ({','.join('?' for _ in values)})", values)
        old.commit()
        old.close()
        migrated = SQLiteState(path)
        try:
            self.assertEqual(tuple(row[1] for row in migrated._db.execute("PRAGMA table_info(help_requests)")), FIELDS)
            self.assertEqual(migrated._db.execute("SELECT * FROM help_requests").fetchone(), ("LEGACY-1", "voice", None, None, *(DETAILS[key] for key in legacy_fields)))
            migrated.put_help_request({"report_id": "LEGACY-1", "channel": "voice", **{key: DETAILS[key] for key in legacy_fields}})
            migrated.put_help_request({"report_id": "FORM-1", "channel": "form", **DETAILS})
            self.assertEqual(migrated._db.execute("SELECT COUNT(*) FROM help_requests").fetchone()[0], 2)
        finally:
            migrated._db.close()
        reopened = SQLiteState(path)
        self.assertEqual(reopened._db.execute("SELECT COUNT(*) FROM help_requests").fetchone()[0], 2)
        reopened._db.close()


if __name__ == "__main__":
    unittest.main()
