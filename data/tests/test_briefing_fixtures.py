"""Checks for the area briefing fixtures (C2, build_briefing_fixtures.py). Stdlib only."""

import json
import unittest
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[2] / "contract" / "fixtures"


def load(name):
    return json.loads((FIXTURES / name).read_text())


def walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk(v)


class Briefing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pb = load("areaBriefing.P-B.json")
        cls.views = {n: load(f"areaBriefing.{n}.json") for n in ("P-A", "P-B", "P-C", "P-B.empty", "P-B.stale", "P-B.layer-missing")}

    def fact(self, doc, key):
        return next(f for f in doc["facts"] if f["key"] == key)

    def test_reviewed_demand_is_24_and_matches_the_cases(self):
        # Pack §7 step 3: C-01 is approved and P-B demand is still 24 (no double count).
        self.assertEqual(self.fact(self.pb, "reviewedDemand")["value"], 24)
        zone_sum = sum(next(f["value"] for f in z["facts"] if f["key"] == "reviewedEvacuation") for z in self.pb["zones"])
        self.assertEqual(zone_sum, 24)
        self.assertEqual(sum(z["badge"]["urgent"] for z in self.pb["zones"]), self.pb["badge"]["urgent"])

    def test_unknown_is_never_zero(self):
        for name, doc in self.views.items():
            for node in walk(doc):
                if "value" in node and node["value"] is None:
                    self.assertTrue(node.get("valueReason"), (name, node.get("key")))

    def test_estimates_stay_out_of_counts(self):
        for doc in self.views.values():
            for f in doc["facts"]:
                self.assertNotIn("estimate", f["basis"].lower(), f["key"])
            self.assertIn("never adds to reviewed counts", doc["estimate"]["label"])

    def test_not_yet_checked_never_exceeds_everyone(self):
        for z in self.pb["zones"]:
            lo, hi = z["estimate"]["notYetChecked"]
            self.assertTrue(0 <= lo <= hi <= z["estimate"]["everyone"][1], z["zoneId"])

    def test_cases_carry_no_exact_location(self):
        # D25: shared views carry landmark-level locations only.
        for z in self.pb["zones"]:
            for c in z["cases"]:
                self.assertFalse({"at", "lat", "lng", "point", "address", "phone", "name"} & set(c), c["caseId"])

    def test_quiet_zone_has_no_reports(self):
        b4 = next(z for z in self.pb["zones"] if z["zoneId"] == "B-4")
        self.assertEqual(b4["status"], "no_reports")
        self.assertGreater(b4["estimate"]["notYetChecked"][1], 0)

    def test_variants(self):
        empty = self.views["P-B.empty"]
        self.assertTrue(all(z["status"] == "no_reports" and not z["cases"] for z in empty["zones"]))
        self.assertLess(self.views["P-B.stale"]["generatedAt"], self.pb["generatedAt"])
        self.assertEqual(self.views["P-B.layer-missing"]["layers"]["floodExtent"]["state"], "unavailable")

    def test_synthetic(self):
        for doc in self.views.values():
            self.assertEqual(doc["dataMode"], "synthetic")


if __name__ == "__main__":
    unittest.main()
