import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_extent_budget import check, polygon_area_m2  # noqa: E402


def square(lon, lat, side_deg):
    return [[[lon, lat], [lon + side_deg, lat], [lon + side_deg, lat + side_deg], [lon, lat + side_deg], [lon, lat]]]


def write(doc):
    tmp = tempfile.NamedTemporaryFile("w", suffix=".geojson", delete=False)
    tmp.write(json.dumps(doc))
    tmp.close()
    return tmp.name


def extent(features, meta=None):
    return {
        "type": "FeatureCollection",
        "features": features,
        "reachpoint": meta if meta is not None else {"label": "Extent on 2025-11-23", "attribution": "Copernicus"},
    }


def feature(coords, **props):
    base = {"package": "hy-2025-11", "acquired": "2025-11-23"}
    return {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": coords}, "properties": {**base, **props}}


class CheckExtentBudget(unittest.TestCase):
    def test_area_of_one_hectare_square(self):
        side = 100 / 111_320  # ~100 m at the equator
        self.assertAlmostEqual(polygon_area_m2(square(0, 0, side)), 10_000, delta=50)

    def test_valid_extent_passes(self):
        errors, summary = check(write(extent([feature(square(100.45, 7.0, 0.005))])))
        self.assertEqual(errors, [])
        self.assertEqual(summary["features"], 1)

    def test_tiny_polygon_fails(self):
        errors, _ = check(write(extent([feature(square(100.45, 7.0, 0.0001))])))
        self.assertTrue(any("under 0.5 ha" in e for e in errors))

    def test_outside_aoi_fails(self):
        errors, _ = check(write(extent([feature(square(101.5, 7.0, 0.005))])))
        self.assertTrue(any("outside" in e for e in errors))

    def test_missing_label_and_date_fail(self):
        f = feature(square(100.45, 7.0, 0.005))
        f["properties"].pop("acquired")
        errors, _ = check(write(extent([f], meta={})))
        self.assertTrue(any("reachpoint.label" in e for e in errors))
        self.assertTrue(any("acquired" in e for e in errors))

    def test_over_budget_fails(self):
        feats = [feature(square(100.31 + (i % 60) * 0.005, 6.86 + (i // 60) * 0.005, 0.004)) for i in range(3000)]
        errors, _ = check(write(extent(feats)))
        self.assertTrue(any("budget" in e for e in errors))

    def test_not_geojson_fails(self):
        errors, _ = check(write({"hello": "world"}))
        self.assertIn("not a GeoJSON FeatureCollection", errors)


if __name__ == "__main__":
    unittest.main()
