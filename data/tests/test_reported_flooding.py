import json
import sys
import unittest
from pathlib import Path

DATA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DATA))
from packages import PACKAGES  # noqa: E402

PATH = DATA / "hy-2025-11" / "reported-flooding.geojson"


class ReportedFlooding(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(PATH.read_text())

    def test_label_and_attribution(self):
        meta = self.doc["reachpoint"]
        self.assertIn("not seen by satellite", meta["label"])
        self.assertIn("OpenStreetMap", meta["attribution"])

    def test_every_point_is_cited_dated_and_inside_aoi(self):
        west, south, east, north = PACKAGES["hy-2025-11"]["bbox"]
        for f in self.doc["features"]:
            p = f["properties"]
            self.assertEqual(f["geometry"]["type"], "Point")
            lon, lat = f["geometry"]["coordinates"]
            self.assertTrue(west <= lon <= east and south <= lat <= north, p["id"])
            self.assertEqual(p["kind"], "qualitative_report")
            self.assertTrue(p["sources"] and all(s.startswith("https://") for s in p["sources"]), p["id"])
            self.assertRegex(p["reported_on"], r"^2025-11-\d\d$")
            self.assertIn("approximate", p["location"])


if __name__ == "__main__":
    unittest.main()
