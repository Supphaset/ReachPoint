"""Caller migration, evidence guards, API review history and private team preparation notes."""

import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from api import main
from api.ai import desk_review as ai
from api.server import desk
from api.server.memory import Clock, MemoryStore
from api.server.sqlite_store import SQLiteMemoryStore, SQLiteState
from api.views.team import team_missions

CALLER = {"report_id": "R-001", "channel": "form", "phone_number": "0000000000", "type": "food",
          "people_details": "Two adults", "n_children": 0, "n_elders": 0, "n_pets": None,
          "location": "Synthetic school", "coordinates": None, "location_details": None,
          "water_level": "Chest deep inside the house", "situation_details": "Safe upstairs; dry road access",
          "emergency_detail": "No immediate danger", "other_details": "Regular medication has run out; name unknown"}


def reading(*items):
    return ai.Reading(evidence=[ai.Evidence(kind=k, field=f, quote=q) for k, f, q in items])


ROUTINE = reading(("routine", "situation_details", "Safe upstairs"),
                  ("dry_access", "situation_details", "dry road access"),
                  ("medication", "other_details", CALLER["other_details"]))


class ClassificationTests(unittest.TestCase):
    def generate(self, evidence, **changes):
        with patch.object(ai, "read_model", return_value=evidence):
            return ai.generate({**CALLER, **changes})

    def test_routine_truck_and_optional_summary_are_supported_by_quotes(self):
        result = self.generate(ROUTINE)
        self.assertEqual((result["emergency_level"], result["transport_recommendation"], result["checked_by"]), ("3", "truck", "AI"))
        self.assertIn("medication has run out", result["volunteer_summary"])
        self.assertNotIn(CALLER["phone_number"], result["volunteer_summary"])
        self.assertEqual(result["clinical_assessment"], "not_assessed")

    def test_deep_indoor_water_does_not_decide_transport(self):
        result = self.generate(reading(("water", "water_level", CALLER["water_level"])))
        self.assertEqual(result["transport_recommendation"], "needs_assessment")
        self.assertIsNone(result["emergency_level"])

    def test_optional_summary_fits_human_review_form_without_cutting_quotes(self):
        fields = {field: field + " " + "x" * 470 for field in ai.FIELDS[:4]}
        evidence = reading(*[("water", field, quote) for field, quote in fields.items()])
        result = self.generate(evidence, **fields)
        self.assertLessEqual(len(result["volunteer_summary"]), 2000)
        for line in result["volunteer_summary"].splitlines():
            self.assertIn(line.removeprefix("Caller reports: "), fields.values())

    def test_flooded_access_boat_and_specialist_hazard_override(self):
        evidence = reading(("flooded_access", "situation_details", "Road cut off by water"))
        result = self.generate(evidence, situation_details="Road cut off by water")
        self.assertEqual(result["transport_recommendation"], "boat")
        result = self.generate(reading(*[(e.kind, e.field, e.quote) for e in evidence.evidence],
                                      ("specialist_hazard", "other_details", "Strong current")),
                               situation_details="Road cut off by water", other_details="Strong current")
        self.assertEqual(result["transport_recommendation"], "needs_assessment")

    def test_conflicting_access_never_chooses_truck(self):
        result = self.generate(reading(("dry_access", "situation_details", "dry road access"),
                                      ("flooded_access", "other_details", "Road cut off by water")),
                               other_details="Road cut off by water")
        self.assertEqual(result["transport_recommendation"], "needs_assessment")

    def test_medical_danger_floor_cannot_be_ranked_routine_by_model(self):
        result = self.generate(ROUTINE, emergency_detail="One adult is unconscious")
        self.assertEqual(result["emergency_level"], "1a")
        self.assertTrue(result["immediate_danger"])
        self.assertEqual(result["review_status"], "human_review_required")

    def test_rescue_danger_and_priority_levels(self):
        result = self.generate(reading(("rescue_emergency", "emergency_detail", "Water reaches our last refuge")),
                               emergency_detail="Water reaches our last refuge")
        self.assertEqual(result["emergency_level"], "1b")
        result = self.generate(reading(("priority", "situation_details", "Need assisted evacuation from safe refuge")),
                               situation_details="Need assisted evacuation from safe refuge")
        self.assertEqual(result["emergency_level"], "2")

    def test_unsupported_quote_or_model_failure_never_becomes_routine(self):
        result = self.generate(reading(("routine", "emergency_detail", "Invented safe circumstances")))
        self.assertIsNone(result["emergency_level"])
        self.assertIsNone(result["volunteer_summary"])
        self.assertIsNone(result["checked_by"])
        with patch.object(ai, "read_model", side_effect=RuntimeError("private diagnostics")):
            result = ai.generate(CALLER)
        self.assertNotIn("private diagnostics", str(result))
        self.assertEqual(result["review_status"], "human_review_required")

    def test_unknown_is_not_routine_and_negated_or_historical_signs_are_not_current(self):
        for text in (None, "Not unconscious", "Was unconscious yesterday; awake now", "If someone becomes unconscious", "ไม่ได้หมดสติ"):
            result = self.generate(reading(), emergency_detail=text)
            self.assertIsNone(result["emergency_level"])
            self.assertFalse(result["immediate_danger"])
        self.assertFalse(ai.generate(CALLER, use_model=False)["checked_by"])

    def test_negated_sign_does_not_hide_another_current_danger(self):
        result = self.generate(reading(), emergency_detail="Not unconscious but cannot breathe")
        self.assertEqual(result["emergency_level"], "1a")

    def test_access_details_are_also_checked_for_reported_danger(self):
        result = self.generate(reading(), location_details="An adult is unconscious near the entrance")
        self.assertEqual(result["emergency_level"], "1a")

    def test_immediate_danger_is_first_even_for_rescue_before_medical(self):
        rows = [{"report_id": "routine", "review": {"emergency_level": "3"}},
                {"report_id": "medical", "review": {"emergency_level": "1a"}},
                {"report_id": "rescue", "review": {"emergency_level": "1b", "immediate_danger": True}}]
        self.assertEqual(sorted(rows, key=ai.sort_key)[0]["report_id"], "rescue")


class DeskApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = main.database, main.memory
        self.db = SQLiteState(str(Path(self.temp.name) / "desk.sqlite3"))
        self.db.put_help_request(CALLER)
        main.database = self.db
        main.memory = SQLiteMemoryStore(self.db, Clock("demo"))
        self.client = TestClient(main.app)
        self.patches = [patch.object(main, "USE_AI", True), patch.object(main, "_schedule_desk_review"),
                        patch.object(ai, "read_model", return_value=ROUTINE)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        main.database, main.memory = self.original
        self.db._db.close()
        self.temp.cleanup()

    def human_body(self, **changes):
        row = self.client.get("/api/desk/R-001").json()
        return {"submissionId": "human-once", "input_revision": row["input_revision"],
                "expected_revision": (row["review"] or {}).get("review_revision", 0),
                "transport_recommendation": "boat", "emergency_level": "2", "immediate_danger": False,
                "volunteer_summary": None, "reviewed_by": "coordinator:synthetic", "reason": "Access checked with the team",
                **changes}

    def test_ai_review_is_persistent_and_never_changes_caller_or_assigns_team(self):
        allocations = copy.deepcopy(main.memory.store.seed["allocations"])
        response = self.client.post("/api/desk/R-001/ai-review", json={"submissionId": "ai-once"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.post("/api/desk/R-001/ai-review", json={"submissionId": "ai-once"}).json(), response.json())
        self.assertEqual(response.json()["value"]["emergency_level"], "3")
        main.memory = SQLiteMemoryStore(self.db, Clock("demo"))
        row = self.client.get("/api/desk/R-001").json()
        self.assertEqual(row["review"]["checked_by"], "AI")
        self.assertEqual(len(row["history"]), 1)
        self.assertEqual(self.db.callers(), [CALLER])
        self.assertEqual(main.memory.store.seed["allocations"], allocations)

    def test_human_override_idempotency_and_ai_rerun_preserve_human_review(self):
        self.client.post("/api/desk/R-001/ai-review", json={"submissionId": "ai-once"})
        body = self.human_body()
        response = self.client.post("/api/desk/R-001/human-review", json=body)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.post("/api/desk/R-001/human-review", json=body).json(), response.json())
        rerun = self.client.post("/api/desk/R-001/ai-review", json={"submissionId": "ai-after-human"}).json()["value"]
        self.assertEqual(rerun, response.json()["value"])
        self.assertEqual(rerun["checked_by"], "Human")
        self.assertIsNone(rerun["volunteer_summary"])
        self.assertEqual(len(self.client.get("/api/desk/R-001").json()["history"]), 2)

    def test_stale_human_review_and_invalid_levels_are_refused(self):
        self.client.post("/api/desk/R-001/ai-review", json={"submissionId": "ai-once"})
        for changes, status in (({"expected_revision": 0}, 409), ({"input_revision": "old"}, 409),
                                ({"emergency_level": "0"}, 422), ({"emergency_level": "3", "immediate_danger": True}, 409),
                                ({"reviewed_by": " "}, 409), ({"reason": " "}, 409)):
            response = self.client.post("/api/desk/R-001/human-review", json=self.human_body(**changes))
            self.assertEqual(response.status_code, status, response.text)
        self.assertEqual(self.client.get("/api/desk/missing").status_code, 404)

    def test_changed_input_marks_old_review_stale(self):
        self.client.post("/api/desk/R-001/ai-review", json={"submissionId": "ai-once"})
        self.db._db.execute("UPDATE callers SET emergency_detail='New danger reported' WHERE report_id='R-001'")
        self.db._db.commit()
        row = self.client.get("/api/desk/R-001").json()
        self.assertTrue(row["review_stale"])
        self.assertIsNone(row["review"]["checked_by"])
        self.assertEqual(row["review"]["review_status"], "human_review_required")

    def test_danger_is_visible_before_ai_review(self):
        self.db._db.execute("UPDATE callers SET emergency_detail='One adult is unconscious' WHERE report_id='R-001'")
        self.db._db.commit()
        row = self.client.get("/api/desk").json()["callers"][0]
        self.assertIsNone(row["review"])
        self.assertTrue(row["immediate_danger"])
        self.assertEqual(row["reported_emergency_level"], "1a")

    def test_human_review_wins_over_ai_result_in_flight(self):
        # Prepare the body before taking the write lock; the API read also takes that lock.
        body = self.human_body()
        def model(_):
            main.memory.write("human-during-ai", lambda: desk.human_review(main.memory, self.db, "R-001", body))
            return ROUTINE
        with patch.object(ai, "read_model", side_effect=model):
            result = self.client.post("/api/desk/R-001/ai-review", json={"submissionId": "ai-once"}).json()["value"]
        self.assertEqual(result["checked_by"], "Human")

    def test_memory_mode_reads_the_same_callers(self):
        main.database = None
        main.memory = MemoryStore()
        main.memory.store.seed["callers"] = {CALLER["report_id"]: CALLER}
        self.assertEqual(self.client.get("/api/desk").json()["callers"][0]["report_id"], CALLER["report_id"])

    def test_reset_during_model_work_cannot_restore_old_callers(self):
        saved_replay = main.flood_replay
        def model(_):
            self.client.post("/api/demo/reset")
            return ROUTINE
        try:
            with patch.object(ai, "read_model", side_effect=model):
                response = self.client.post("/api/desk/R-001/ai-review", json={"submissionId": "reset-in-flight"})
            self.assertEqual(response.status_code, 409)
            self.assertEqual(self.db.callers(), [])
            self.assertEqual(self.client.get("/api/desk").json()["callers"], [])
        finally:
            main.flood_replay = saved_replay


class MigrationAndPrivacyTests(unittest.TestCase):
    def test_current_legacy_table_is_renamed_without_losing_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "legacy.sqlite3")
            db = SQLiteState(path)
            db.put_help_request(CALLER)
            db._db.execute("ALTER TABLE callers RENAME TO help_requests")
            db._db.commit()
            db._db.close()
            migrated = SQLiteState(path)
            self.assertEqual(migrated.callers(), [CALLER])
            self.assertIsNone(migrated._db.execute("SELECT 1 FROM sqlite_master WHERE name='help_requests'").fetchone())
            migrated._db.close()

    def test_preparation_note_is_only_in_accepted_active_job(self):
        memory = MemoryStore()
        case = next(c for c in memory.store.cases if c["caseId"] == "C-01")
        case["fromReport"] = "SYNTHETIC-REPORT"
        memory.store.seed["callerReviews"] = {"SYNTHETIC-REPORT": {
            "volunteer_summary": "Synthetic medication request", "checked_by": "AI", "reviewed_at": memory.clock.iso()}}
        before = team_missions(memory.store, "T-S", memory.clock.iso())
        self.assertNotIn("Synthetic medication request", str(before["open"]))
        listing = next(r for r in before["open"] if r["caseId"] == "C-01")
        result = memory.write("take", lambda: memory.claim(listing["listingId"], "T-S", [listing["groups"][0]["groupId"]], listing["needRevision"]))
        jobs = team_missions(memory.store, "T-S", memory.clock.iso())["jobs"]
        job = next(j for j in jobs if j["allocationId"] == result["value"]["allocationId"])
        self.assertIn("Synthetic medication request", job["preparationSummary"]["text"])
        allocation = next(a for a in memory.store.seed["allocations"] if a["allocationId"] == job["allocationId"])
        allocation.update(state="closed", outcome="done")
        closed = team_missions(memory.store, "T-S", memory.clock.iso())["jobs"]
        self.assertNotIn("preparationSummary", next(j for j in closed if j["allocationId"] == job["allocationId"]))


if __name__ == "__main__":
    unittest.main()
