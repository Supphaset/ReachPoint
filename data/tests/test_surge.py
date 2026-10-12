"""Reproducible synthetic intake with evaluation truth kept out of processing."""
import json
import unittest
from collections import Counter
from pathlib import Path

from data.surge import generate

CATALOGUE = json.loads((Path(__file__).resolve().parents[2] / "contract/fixtures/areas.hy-2025-11.json").read_text())


class Surge(unittest.TestCase):
    def test_reproducible_size_categories_and_channels(self):
        rows, truth = generate(CATALOGUE)
        self.assertEqual((rows, truth), generate(CATALOGUE))
        self.assertEqual(len(rows), 1200)
        self.assertEqual(len({r["submissionId"] for r in rows}), 1200)
        self.assertEqual(Counter(t["category"] for t in truth),
                         {"routine": 600, "urgent": 150, "update": 150, "water": 120, "ambiguous": 120, "invalid": 60})
        self.assertEqual(Counter(r["channel"] for r in rows), {"text": 800, "simulated_call": 400})
        self.assertTrue(all(r["synthetic"] for r in rows))

    def test_generation_truth_and_identity_never_reach_intake(self):
        rows, truth = generate(CATALOGUE)
        self.assertTrue(all("category" not in r and "expectedSegment" not in r and "householdId" not in r for r in rows))
        self.assertTrue(any("earlier report" in r["text"] for r in rows))
        self.assertTrue(any(t["conflictingMeasurement"] for t in truth))
        refs = [t["observationReference"] for t in truth if t["category"] not in ("ambiguous", "invalid")]
        self.assertLess(len(set(refs)), len(refs))
        segments = {s["id"] for z in CATALOGUE["zones"] for s in z["segments"]}
        self.assertEqual({t["expectedSegment"] for t in truth if t["expectedSegment"]}, segments)

    def test_other_seed_changes_intake_without_using_real_data(self):
        rows, _ = generate(CATALOGUE, seed=43)
        self.assertNotEqual(rows, generate(CATALOGUE)[0])
        self.assertTrue(all(set(r) == {"reportId", "submissionId", "channel", "receivedAt", "text", "synthetic"} for r in rows))


if __name__ == "__main__":
    unittest.main()
