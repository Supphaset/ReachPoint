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
        self.assertEqual(result["emergency_level"], "2")

    def test_reported_numeric_water_uses_fifty_cm_planning_threshold(self):
        for amount, expected in ((49, "truck"), (50, "boat"), (51, "boat")):
            text = f"Reported water depth is {amount} cm"
            result = self.generate(ai.Reading(evidence=[], water_depths=[ai.WaterDepth(
                field="water_level", quote=text, depth_cm=amount, scope="access")]), water_level=text)
            self.assertEqual(result["transport_recommendation"], expected)
            self.assertEqual(result["reported_water_depth_cm"], amount)
            self.assertEqual(result["transport_threshold_cm"], 50)
            self.assertFalse(result["approved"])

    def test_units_conflicting_depths_and_invented_depth(self):
        text = "ระดับน้ำ 0.5 เมตร"
        result = self.generate(ai.Reading(evidence=[], water_depths=[ai.WaterDepth(
            field="water_level", quote=text, depth_cm=50, scope="inside")]), water_level=text)
        self.assertEqual(result["transport_recommendation"], "boat")
        text = "น้ำท่วมชั้นหนึ่ง"
        result = self.generate(ai.Reading(evidence=[], water_depths=[ai.WaterDepth(
            field="water_level", quote=text, depth_cm=100, scope="inside")]), water_level=text)
        self.assertIsNone(result["checked_by"])
        self.assertEqual(result["transport_recommendation"], "needs_assessment")
        evidence = ai.Reading(evidence=[], water_depths=[
            ai.WaterDepth(field="water_level", quote="20 cm", depth_cm=20, scope="access"),
            ai.WaterDepth(field="water_level", quote="70 cm", depth_cm=70, scope="access")])
        result = self.generate(evidence, water_level="One report says 20 cm; another says 70 cm")
        self.assertEqual(result["transport_recommendation"], "needs_assessment")

    def test_active_food_and_water_request_is_level_two(self):
        text = "มีเด็ก 2 คน หิวข้าวและน้ำ"
        result = self.generate(reading(("assistance_need", "people_details", text)), people_details=text)
        self.assertEqual(result["emergency_level"], "2")
        self.assertFalse(result["immediate_danger"])

    def test_chest_water_suggests_boat_without_inventing_centimetres(self):
        text = "น้ำท่วมถึงอก"
        result = self.generate(reading(("deep_water", "situation_details", text)), situation_details=text)
        self.assertEqual(result["transport_recommendation"], "boat")
        self.assertIsNone(result["reported_water_depth_cm"])
        self.assertEqual(result["transport_basis"], "qualitative_water")
        self.assertEqual(result["emergency_level"], "2")
        self.assertFalse(result["immediate_danger"])

    def test_help_type_defaults_to_assistance_without_claiming_absence_of_danger(self):
        result = self.generate(reading(), people_details=None, situation_details=None, water_level=None)
        self.assertEqual(result["emergency_level"], "2")
        self.assertEqual(result["clinical_assessment"], "not_assessed")
        self.assertFalse(result["approved"])

    def test_numeric_depth_does_not_bypass_hazards_or_establish_shallow_indoor_access(self):
        depth = ai.WaterDepth(field="water_level", quote="60 cm", depth_cm=60, scope="access")
        result = self.generate(ai.Reading(water_depths=[depth], evidence=[
            ai.Evidence(kind="specialist_hazard", field="other_details", quote="Strong current")]),
            water_level="60 cm", other_details="Strong current")
        self.assertEqual(result["transport_recommendation"], "needs_assessment")
        depth = ai.WaterDepth(field="water_level", quote="20 cm", depth_cm=20, scope="inside")
        result = self.generate(ai.Reading(evidence=[], water_depths=[depth]), water_level="20 cm")
        self.assertEqual(result["transport_recommendation"], "needs_assessment")
        for text in ("Yesterday 60 cm", "If water reaches 60 cm", "ไม่ถึง 60 ซม.", "20-60 cm"):
            self.assertFalse(ai.supported_depth({"water_level": text}, ai.WaterDepth(
                field="water_level", quote=text, depth_cm=60, scope="access")))

    def test_optional_summary_fits_human_review_form_without_cutting_quotes(self):
        fields = {field: field + " " + "x" * 470 for field in ai.FIELDS[:4]}
        evidence = reading(*[("water", field, quote) for field, quote in fields.items()])
        result = self.generate(evidence, **fields)
        self.assertLessEqual(len(result["volunteer_summary"]), 2000)
        for line in result["volunteer_summary"].splitlines():
            self.assertIn(line.removeprefix("Caller reports: "), fields.values())

    def test_preparation_combines_overlapping_thai_quotes_without_repeated_prefix(self):
        result = self.generate(reading(
            ("mobility", "people_details", "ผู้ป่วยติดเตียง"),
            ("medication", "other_details", "ต้องการยา"),
            ("assistance_need", "situation_details", "มีผู้ป่วยติดเตียงต้องการยา")),
            people_details="ผู้ป่วยติดเตียง", other_details="ต้องการยา",
            situation_details="มีผู้ป่วยติดเตียงต้องการยา")
        self.assertEqual(result["volunteer_summary"], "มีผู้ป่วยติดเตียงต้องการยา")
        self.assertEqual(len(result["evidence"]), 4)  # Quotes remain available separately, including help type.

    def test_preparation_keeps_distinct_needs_from_the_same_field(self):
        result = self.generate(reading(
            ("medication", "other_details", "Insulin has run out"),
            ("medication", "other_details", "Bring the medication list")),
            other_details="Insulin has run out. Bring the medication list")
        self.assertIn("Insulin has run out", result["volunteer_summary"])
        self.assertIn("Bring the medication list", result["volunteer_summary"])

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
            result = self.generate(reading(), emergency_detail=text, type=None)
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

    def test_stored_notes_are_compacted_without_rewriting_review_or_history(self):
        self.client.post("/api/desk/R-001/ai-review", json={"submissionId": "ai-once"})
        legacy = "Caller reports: ผู้ป่วยติดเตียง\nCaller reports: ต้องการยา\nCaller reports: มีผู้ป่วยติดเตียงต้องการยา"
        main.memory.store.seed["callerReviews"]["R-001"]["volunteer_summary"] = legacy
        original = copy.deepcopy(main.memory.store.seed)
        row = self.client.get("/api/desk/R-001").json()
        self.assertEqual(row["review"]["volunteer_summary"], "มีผู้ป่วยติดเตียงต้องการยา")
        self.assertEqual(main.memory.store.seed, original)

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

    def test_approval_allows_unresolved_location_and_optional_notes(self):
        self.client.post("/api/desk/R-001/ai-review", json={"submissionId": "ai-once"})
        row = self.client.get("/api/desk/R-001").json()
        self.assertFalse(row["review"]["approved"])
        self.assertEqual(row["review"]["review_status"], "human_review_required")
        body = self.human_body(approve=True)
        response = self.client.post("/api/desk/R-001/human-review", json=body)
        self.assertEqual(response.status_code, 200, response.text)
        approved = response.json()["value"]
        self.assertTrue(approved["approved"])
        self.assertEqual(approved["approved_by"], "coordinator:synthetic")
        self.assertIsNone(approved["resolved_location"]["latitude"])
        self.assertIsNone(approved["resolved_location"]["longitude"])
        self.assertIsNone(approved["volunteer_summary"])
        self.assertEqual(self.db.callers(), [CALLER])
        self.assertEqual(self.client.post("/api/desk/R-001/human-review", json=body).json(), response.json())
        self.db._db.execute("UPDATE callers SET situation_details='New report' WHERE report_id='R-001'")
        self.db._db.commit()
        stale = self.client.get("/api/desk/R-001").json()
        self.assertFalse(stale["review"]["approved"])
        self.assertIsNone(stale["review"]["approved_at"])
        self.assertTrue(stale["history"][-1]["approved"])

    def test_corrections_clear_approval_and_cannot_spoof_location_source(self):
        self.client.post("/api/desk/R-001/ai-review", json={"submissionId": "ai-once"})
        location = {"address": "Synthetic school address", "latitude": 7.0, "longitude": 100.5, "source": "google_maps_geocoding"}
        body = self.human_body(approve=True, resolved_location=location)
        self.assertEqual(self.client.post("/api/desk/R-001/human-review", json=body).status_code, 200)
        body = self.human_body(submissionId="correct-again", resolved_location={**location, "address": "Corrected synthetic school"})
        response = self.client.post("/api/desk/R-001/human-review", json=body)
        self.assertEqual(response.status_code, 200, response.text)
        corrected = response.json()["value"]
        self.assertFalse(corrected["approved"])
        self.assertIsNone(corrected["approved_at"])
        self.assertEqual(corrected["resolved_location"]["source"], "human")
        self.assertEqual(self.client.get("/api/desk").json()["counts"]["needs_review"], 1)

    def test_approval_allows_unresolved_transport_and_urgency(self):
        self.client.post("/api/desk/R-001/ai-review", json={"submissionId": "ai-once"})
        location = {"address": "Synthetic school", "latitude": 7.0, "longitude": 100.5}
        for i, fields in enumerate(({"emergency_level": None}, {"transport_recommendation": "needs_assessment"},
                                    {"emergency_level": None, "transport_recommendation": None})):
            body = self.human_body(submissionId=f"optional-{i}", approve=True, resolved_location=location, **fields)
            response = self.client.post("/api/desk/R-001/human-review", json=body)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertTrue(response.json()["value"]["approved"])

    def test_approval_requires_only_original_phone_type_and_location(self):
        for field in ("phone_number", "type", "location"):
            for missing in ((None,) if field == "type" else (None, "  ")):
                with self.subTest(field=field, missing=missing):
                    self.db._db.execute(f"UPDATE callers SET {field}=? WHERE report_id='R-001'", (missing,))
                    self.db._db.commit()
                    response = self.client.post("/api/desk/R-001/human-review", json=self.human_body(approve=True))
                    self.assertEqual(response.status_code, 409, response.text)
                    self.assertIn("INCOMPLETE_REVIEW", response.text)
            self.db._db.execute(f"UPDATE callers SET {field}=? WHERE report_id='R-001'", (CALLER[field],))
            self.db._db.commit()

    def test_minimal_approval_without_ai_keeps_unknown_fields_and_danger(self):
        for field in CALLER:
            if field not in ("report_id", "channel", "phone_number", "type", "location"):
                self.db._db.execute(f"UPDATE callers SET {field}=NULL WHERE report_id='R-001'")
        self.db._db.commit()
        body = self.human_body(approve=True, emergency_level=None, transport_recommendation=None, immediate_danger=True)
        response = self.client.post("/api/desk/R-001/human-review", json=body)
        self.assertEqual(response.status_code, 200, response.text)
        review = response.json()["value"]
        self.assertTrue(review["approved"])
        self.assertTrue(review["immediate_danger"])
        self.assertIsNone(review["emergency_level"])
        self.assertEqual(review["transport_recommendation"], "needs_assessment")
        self.assertEqual(review["review_status"], "human_reviewed")
        self.assertIsNone(review["volunteer_summary"])
        self.assertEqual(review["resolved_location"]["status"], "unresolved")

    def test_danger_is_visible_before_ai_review(self):
        self.db._db.execute("UPDATE callers SET emergency_detail='One adult is unconscious' WHERE report_id='R-001'")
        self.db._db.commit()
        row = self.client.get("/api/desk").json()["callers"][0]
        self.assertIsNone(row["review"])
        self.assertTrue(row["immediate_danger"])
        self.assertEqual(row["reported_emergency_level"], "1a")

    def test_human_review_wins_over_ai_result_in_flight(self):
        # Prepare the body before taking the write lock; the API read also takes that lock.
        body = self.human_body(approve=True, transport_recommendation=None, emergency_level=None)
        def model(_):
            main.memory.write("human-during-ai", lambda: desk.human_review(main.memory, self.db, "R-001", body))
            return ROUTINE
        with patch.object(ai, "read_model", side_effect=model):
            result = self.client.post("/api/desk/R-001/ai-review", json={"submissionId": "ai-once"}).json()["value"]
        self.assertEqual(result["checked_by"], "Human")
        self.assertTrue(result["approved"])
        self.assertIsNone(result["emergency_level"])

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

    def test_human_approval_advances_only_the_caller_review_step(self):
        main.memory.store.seed.setdefault("reports", []).append({
            "reportId": "R-001", "status": "proposed", "receivedAt": "2026-10-15T03:00:00Z"})
        main.memory.store.seed.setdefault("statusTokens", {})["synthetic-status"] = {"reportId": "R-001", "caseId": None}
        path = "/api/status/synthetic-status"
        before = self.client.get(path).json()
        self.assertEqual(before["state"], "received")
        self.client.post("/api/desk/R-001/ai-review", json={"submissionId": "ai-once"})
        self.assertEqual(self.client.get(path).json()["state"], "received")
        allocations = copy.deepcopy(main.memory.store.seed["allocations"])
        body = self.human_body(approve=True, transport_recommendation=None, emergency_level=None)
        approved = self.client.post("/api/desk/R-001/human-review", json=body).json()["value"]
        current = self.client.get(path).json()
        self.assertEqual(current["state"], "reviewed")
        self.assertEqual(current["lines"][0]["state"], "reviewed")
        self.assertEqual(current["completedAt"], [before["completedAt"][0], approved["approved_at"], None, None])
        self.assertNotIn("caseId", current)
        self.assertNotIn("volunteer_summary", str(current))
        self.assertNotIn(CALLER["phone_number"], str(current))
        self.assertEqual(main.memory.store.seed["allocations"], allocations)
        main.memory = SQLiteMemoryStore(self.db, Clock("demo"))
        self.assertEqual(self.client.get(path).json()["state"], "reviewed")
        corrected = self.human_body(submissionId="clear-approval")
        self.client.post("/api/desk/R-001/human-review", json=corrected)
        self.assertEqual(self.client.get(path).json()["state"], "received")

    def test_changed_caller_details_do_not_claim_current_approved_progress(self):
        main.memory.store.seed.setdefault("reports", []).append({"reportId": "R-001", "status": "proposed"})
        main.memory.store.seed.setdefault("statusTokens", {})["synthetic-status"] = {"reportId": "R-001", "caseId": None}
        location = {"address": "Synthetic school", "latitude": 7.0, "longitude": 100.5}
        self.client.post("/api/desk/R-001/human-review", json=self.human_body(approve=True, resolved_location=location))
        self.db._db.execute("UPDATE callers SET situation_details='Changed synthetic report' WHERE report_id='R-001'")
        self.db._db.commit()
        current = self.client.get("/api/status/synthetic-status").json()
        self.assertEqual(current["state"], "received")
        self.assertIsNone(current["completedAt"][1])


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
        self.assertNotIn("preparationSummary", job)
        memory.store.seed["callerReviews"]["SYNTHETIC-REPORT"].update(approved=True, checked_by="Human")
        jobs = team_missions(memory.store, "T-S", memory.clock.iso())["jobs"]
        job = next(j for j in jobs if j["allocationId"] == result["value"]["allocationId"])
        self.assertIn("Synthetic medication request", job["preparationSummary"]["text"])
        allocation = next(a for a in memory.store.seed["allocations"] if a["allocationId"] == job["allocationId"])
        allocation.update(state="closed", outcome="done")
        closed = team_missions(memory.store, "T-S", memory.clock.iso())["jobs"]
        self.assertNotIn("preparationSummary", next(j for j in closed if j["allocationId"] == job["allocationId"]))


if __name__ == "__main__":
    unittest.main()
