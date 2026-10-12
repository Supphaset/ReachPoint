"""Checks for the planning geography (build_geography.py) and the "no satellite data" mask. Stdlib only."""

import json
import math
import sys
import unittest
from pathlib import Path

DATA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DATA))
from packages import MAX_BYTES, PACKAGES  # noqa: E402

PKG = DATA / "hy-2025-11"


def load(name):
    return json.loads((PKG / name).read_text())


def rings(geom):
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    return polys


def in_ring(pt, ring):
    x, y = pt
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def contains(geom, pt):
    return any(in_ring(pt, p[0]) and not any(in_ring(pt, h) for h in p[1:]) for p in rings(geom))


def area_m2(geom):
    kx, ky = 111_320 * math.cos(math.radians(7.0)), 110_574
    total = 0.0
    for p in rings(geom):
        for i, ring in enumerate(p):
            a = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:])) / 2 * kx * ky
            total += abs(a) if i == 0 else -abs(a)
    return total


def grid(geom, n=25):
    xs = [c[0] for c in rings(geom)[0][0]]
    ys = [c[1] for c in rings(geom)[0][0]]
    for i in range(n):
        for j in range(n):
            pt = (min(xs) + (max(xs) - min(xs)) * (i + 0.5) / n, min(ys) + (max(ys) - min(ys)) * (j + 0.5) / n)
            if contains(geom, pt):
                yield pt


class Geography(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.areas = load("areas.geojson")["features"]
        cls.zones = load("zones.geojson")["features"]
        cls.segments = load("segments.geojson")["features"]
        cls.marks = load("landmarks.geojson")["features"]
        cls.catalogue = json.loads((DATA.parent / "contract" / "fixtures" / "areas.hy-2025-11.json").read_text())
        cls.seg_by_id = {f["properties"]["id"]: f for f in cls.segments}

    def test_synthetic_and_labelled(self):
        for name in ("areas", "zones", "segments", "landmarks"):
            meta = load(f"{name}.geojson")["reachpoint"]
            self.assertEqual(meta["dataMode"], "synthetic")
            self.assertIn("not official boundaries or real buildings", meta["label"])

    def test_ids_are_unique_and_linked(self):
        for fs in (self.areas, self.zones, self.segments, self.marks):
            ids = [f["properties"]["id"] for f in fs]
            self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual({f["properties"]["id"] for f in self.areas}, {"P-A", "P-B", "P-C"})
        city = {z["properties"]["id"] for z in self.zones if z["properties"]["areaId"] == "P-B"}
        self.assertLessEqual({"B-1", "B-2", "B-3", "B-4", "B-5"}, city)  # named in the demo scenes
        for z in self.zones:
            p = z["properties"]
            self.assertEqual(p["segmentIds"], [s["properties"]["id"] for s in self.segments
                                               if s["properties"]["zoneId"] == p["id"]])
        for s in self.segments:
            self.assertEqual(s["properties"]["landmarkId"], s["properties"]["id"])  # one segment per landmark
        self.assertEqual(sum(len(z["segments"]) for z in self.catalogue["zones"]), len(self.segments))

    def test_scenario_landmarks_exist(self):
        # Named in the design doc and the demo script.
        for sid in ("B-3-L3", "B-3-L5", "B-4-L5"):
            self.assertIn(sid, self.seg_by_id)
        self.assertEqual(self.seg_by_id["B-3-L3"]["properties"]["label"], "B-3 · L3 Community building")
        self.assertEqual(self.seg_by_id["B-4-L5"]["properties"]["label"], "B-4 · L5 School")

    def test_landmark_sits_in_its_own_segment(self):
        for m in self.marks:
            p = m["properties"]
            if p["kind"] == "destination":
                continue
            self.assertTrue(contains(self.seg_by_id[p["segmentId"]]["geometry"], m["geometry"]["coordinates"]), p["id"])

    def test_segments_tile_each_zone(self):
        for z in self.zones:
            segs = [self.seg_by_id[s]["geometry"] for s in z["properties"]["segmentIds"]]
            self.assertAlmostEqual(sum(area_m2(g) for g in segs) / area_m2(z["geometry"]), 1.0, delta=0.005)
            for pt in grid(z["geometry"]):
                self.assertLessEqual(sum(contains(g, pt) for g in segs), 1, (z["properties"]["id"], pt))

    def test_zones_do_not_overlap_and_stay_in_aoi(self):
        west, south, east, north = PACKAGES["hy-2025-11"]["bbox"]
        for z in self.zones:
            for x, y in rings(z["geometry"])[0][0]:
                self.assertTrue(west <= x <= east and south <= y <= north)
            others = [o["geometry"] for o in self.zones if o is not z]
            for pt in grid(z["geometry"], 15):
                self.assertFalse(any(contains(g, pt) for g in others), z["properties"]["id"])

    def test_city_zones_sit_inside_one_district_and_the_municipality(self):
        districts = load("districts.geojson")["features"]
        self.assertEqual({d["properties"]["id"] for d in districts}, {"เขต 1", "เขต 2", "เขต 3", "เขต 4"})
        muni = load("osm-municipality.geojson")["features"][0]["geometry"]
        for z in self.zones:
            p = z["properties"]
            if p["areaId"] != "P-B":
                self.assertIsNone(p.get("district"))
                continue
            self.assertIn(p["district"], {"เขต 1", "เขต 2", "เขต 3", "เขต 4"})
            home = next(d for d in districts if d["properties"]["id"] == p["district"])
            self.assertIn(p["id"], home["properties"]["zoneIds"])
            for pt in list(grid(z["geometry"], 8)):
                self.assertTrue(contains(muni, pt), p["id"])

    def test_scene_zones(self):
        # B-3 holds the most reported flooding; B-4 none (the quiet-zone scene).
        rep = [f["geometry"]["coordinates"] for f in load("reported-flooding.geojson")["features"]]
        count = {z["properties"]["id"]: sum(contains(z["geometry"], r) for r in rep) for z in self.zones}
        self.assertEqual(max(count, key=count.get), "B-3")
        self.assertEqual(count["B-4"], 0)

    def test_shelter_is_outside_every_zone(self):
        d1 = next(m for m in self.marks if m["properties"]["id"] == "D1")
        self.assertFalse(any(contains(z["geometry"], d1["geometry"]["coordinates"]) for z in self.zones))

    def test_no_satellite_data_share_is_a_fraction(self):
        for f in self.zones + self.segments:
            self.assertTrue(0 <= f["properties"]["noSatelliteDataShare"] <= 1)


class Estimate(unittest.TestCase):
    """People per segment (D27, D31): ranges, never counts."""

    @classmethod
    def setUpClass(cls):
        cls.segments = load("segments.geojson")
        cls.zones = load("zones.geojson")["features"]
        cls.exposure = load("exposure.json")

    def test_label_never_says_victims(self):
        self.assertIn("Never a count of victims", self.exposure["label"])
        self.assertIn("never adds to reviewed counts", self.segments["reachpoint"]["estimate"]["label"])
        self.assertIn("model", self.segments["reachpoint"]["estimate"]["modelLabel"])

    def test_every_segment_has_ordered_ranges(self):
        for f in self.segments["features"] + self.zones:
            e = f["properties"]["estimate"]
            for key in ("everyone", "inSatelliteExtent"):
                lo, hi = e[key]
                self.assertTrue(isinstance(lo, int) and isinstance(hi, int) and 0 <= lo <= hi, (f["properties"]["id"], key))
            self.assertLessEqual(e["inSatelliteExtent"][1], e["everyone"][1])

    def test_model_only_in_blind_city_segments(self):
        for f in self.segments["features"]:
            p, e = f["properties"], f["properties"]["estimate"]
            blind_city = p["areaId"] == "P-B" and p["noSatelliteDataShare"] >= 0.5
            if e["modelledFlooded"] is None:
                self.assertEqual(e["basis"], "satellite")
                continue
            self.assertTrue(blind_city, p["id"])
            self.assertEqual(e["basis"], "model")
            self.assertLessEqual(e["modelledFlooded"][1], e["everyone"][1], p["id"])

    def test_hot_zone_is_modelled_as_flooded(self):
        b3 = next(z for z in self.zones if z["properties"]["id"] == "B-3")["properties"]["estimate"]
        self.assertGreater(b3["modelledFlooded"][1], 0)

    def test_zone_range_matches_its_segments(self):
        by_id = {f["properties"]["id"]: f["properties"]["estimate"] for f in self.segments["features"]}
        for z in self.zones:
            segs = [by_id[s] for s in z["properties"]["segmentIds"]]
            lo, hi = z["properties"]["estimate"]["everyone"]
            self.assertLessEqual(sum(s["everyone"][0] for s in segs), hi * 1.01)
            self.assertLessEqual(lo, sum(s["everyone"][1] for s in segs) * 1.01)

    def test_depth_is_ground_plus_model_band_only_where_modelled(self):
        # D32: every segment has ground height for live caller depths; the depth band is a model, city only.
        for f in self.segments["features"]:
            p, d = f["properties"], f["properties"]["depth"]
            g = d["groundM"]
            self.assertTrue(g[0] <= g[1] <= g[2], p["id"])
            if d["modelledM"] is None:
                continue
            self.assertEqual(p["estimate"]["basis"], "model", p["id"])
            lo, hi = d["modelledM"]
            cap = max(h for _, h in self.exposure["reportedDepthM"].values())
            self.assertTrue(0 <= lo <= hi <= cap, (p["id"], lo, hi))  # never deeper than any report

    def test_fixture_carries_the_estimate(self):
        cat = json.loads((DATA.parent / "contract" / "fixtures" / "areas.hy-2025-11.json").read_text())
        for z in cat["zones"]:
            self.assertIn("everyone", z["estimate"])
            for s in z["segments"]:
                self.assertIn("inSatelliteExtent", s["estimate"])


class NoSatelliteData(unittest.TestCase):
    def test_label_size_and_kind(self):
        path = PKG / "no-satellite-data.geojson"
        doc = json.loads(path.read_text())
        self.assertLessEqual(path.stat().st_size, MAX_BYTES)
        self.assertIn("Never shown as dry", doc["reachpoint"]["label"])
        self.assertIn("WorldCover", doc["reachpoint"]["attribution"])
        self.assertTrue(all(f["properties"]["kind"] == "no_satellite_data" for f in doc["features"]))

    def test_covers_the_reported_city_centre(self):
        # D26 evidence: the satellite saw almost nothing where the news reported deep water.
        mask = [f["geometry"] for f in load("no-satellite-data.geojson")["features"]]
        pts = [f["geometry"]["coordinates"] for f in load("reported-flooding.geojson")["features"]]
        inside = sum(any(contains(g, p) for g in mask) for p in pts)
        self.assertGreaterEqual(inside, len(pts) - 1)


if __name__ == "__main__":
    unittest.main()
