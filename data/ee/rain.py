"""Satellite rain per area for the replayed event (D41): python data/ee/rain.py --project YOUR_EE_PROJECT

Writes data/<package>/rain-imerg.json: the half-hourly NASA GPM IMERG V07 rain estimate (mm in each half hour),
averaged over each area (P-A, P-B, P-C). The app replays it on the demo clock; it never calls Earth Engine live.

IMERG cells are about 10 km, so all three areas see nearly the same rain: use it for the whole city, not to tell
zones apart. It is a satellite estimate and under-reads heavy tropical storms (21 Nov 2025: ~123 mm here against the
335 mm gauge report). Rain is never turned into water depth (requirements: depth, rain, gauges and forecasts stay
distinct).
"""

import argparse
import json
import sys
from pathlib import Path

import ee

DATA_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DATA_DIR))
from packages import PACKAGES  # noqa: E402

COLLECTION = "NASA/GPM_L3/IMERG_V07"
WINDOW = {"hy-2025-11": ("2025-11-18T00:00:00Z", "2025-11-30T00:00:00Z")}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True, help="Google Cloud project registered for Earth Engine")
    parser.add_argument("--package", default="hy-2025-11", choices=sorted(WINDOW))
    args = parser.parse_args()
    ee.Initialize(project=args.project)

    folder = DATA_DIR / args.package
    areas = json.loads((folder / "areas.geojson").read_text())["features"]
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry(f["geometry"]), {"areaId": f["properties"]["id"]}) for f in areas])
    start, end = WINDOW[args.package]
    images = ee.ImageCollection(COLLECTION).filterDate(start, end).select("precipitation")  # mm/hr per half hour

    def per_image(img):
        stats = img.reduceRegions(fc, ee.Reducer.mean(), 1000)
        return stats.map(lambda f: f.set("t", img.date().format("YYYY-MM-dd'T'HH:mm'Z'", "UTC")).setGeometry(None))

    rows = images.map(per_image).flatten().getInfo()["features"]
    series: dict[str, list] = {f["properties"]["id"]: [] for f in areas}
    for r in rows:
        p = r["properties"]
        mm = None if p.get("mean") is None else round(p["mean"] * 0.5, 2)  # rate over half an hour → mm
        series[p["areaId"]].append([p["t"], mm])
    for v in series.values():
        v.sort()
    out = {
        "package": args.package,
        "source": "NASA GPM IMERG V07 Final Run, half-hourly (Earth Engine NASA/GPM_L3/IMERG_V07), mean over each area",
        "label": "Rain (satellite estimate). Often under-reads heavy storms; not water depth",
        "unit": "mm in the half hour starting at t (UTC)",
        "cellKm": 10,
        "window": [start, end],
        "areas": series,
    }
    path = folder / "rain-imerg.json"
    path.write_text(json.dumps(out, separators=(",", ":")) + "\n")
    print(f"  {path.relative_to(DATA_DIR.parent)}: {sum(len(v) for v in series.values())} values")


if __name__ == "__main__":
    main()
