"""Sentinel-1 flood check for ReachPoint (pack §5.1c).

Three steps, run from the repo root with your sandbox Google Cloud project:

    python data/ee/flood_check.py list    --project YOUR_EE_PROJECT --package hy-2025-11
    python data/ee/flood_check.py detect  --project YOUR_EE_PROJECT --package hy-2025-11
    python data/ee/flood_check.py compare --project YOUR_EE_PROJECT --package hy-2025-11 \
        --reference path/to/eos-hatyai.geojson

`list` writes the available scenes, `detect` writes the flood extent GeoJSON,
`compare` measures agreement with a published map. Nothing here runs in the app;
the outputs are committed under data/<package>/ and served from Cloud Storage.
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import ee

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages import ATTRIBUTION, LABEL, MIN_POLYGON_M2, PACKAGES, SIMPLIFY_M  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1]

# Change-detection defaults. VV backscatter drops sharply over new open water.
DEFAULTS = {
    "diff_db": -3.0,        # event minus baseline, VV, dB
    "water_db": -15.0,      # event VV must be at least this dark
    "smooth_m": 30,         # focal median radius against speckle
    "max_slope_deg": 5,     # flood water does not sit on steep slopes
    "perm_water_pct": 80,   # JRC occurrence above this is permanent water, not flood
    "min_pixels": 8,        # connected pixels at 10 m; removes isolated noise
    "scale_m": 20,          # vectorisation scale
}


def s1_collection(aoi, start, end):
    return (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(aoi)
        .filterDate(start, end)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.eq("resolution_meters", 10))
    )


def scene_rows(collection):
    def to_feature(img):
        return ee.Feature(None, {
            "id": img.get("system:index"),
            "time": ee.Date(img.get("system:time_start")).format("YYYY-MM-dd'T'HH:mm"),
            "platform": ee.String("S1").cat(ee.String(img.get("platform_number"))),
            "pass": img.get("orbitProperties_pass"),
            "orbit": img.get("relativeOrbitNumber_start"),
            "polarisations": ee.List(img.get("transmitterReceiverPolarisation")).join("+"),
        })

    feats = collection.map(to_feature).getInfo()["features"]
    return sorted((f["properties"] for f in feats), key=lambda r: r["time"])


def cmd_list(args, pkg, aoi):
    rows = []
    for window_name in ("baseline", "event"):
        start, end = pkg[window_name]
        for row in scene_rows(s1_collection(aoi, start, end)):
            rows.append({"window": window_name, **row})
    out = DATA_DIR / args.package / "scenes.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["window", "time", "platform", "pass", "orbit", "polarisations", "id"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} scenes -> {out.relative_to(DATA_DIR.parent)}")
    for r in rows:
        print(f"  {r['window']:8} {r['time']}  {r['platform']}  {r['pass']:10} orbit {r['orbit']}")
    event_orbits = {r["orbit"] for r in rows if r["window"] == "event"}
    base_orbits = {r["orbit"] for r in rows if r["window"] == "baseline"}
    missing = sorted(event_orbits - base_orbits)
    if missing:
        print(f"WARNING: event orbits {missing} have no baseline scene; detect will skip them.")


def smooth_vv(img, radius_m):
    return img.select("VV").focalMedian(radius_m, "circle", "meters")


def flood_for_date(aoi, pkg, date, orbit, p):
    """Flood mask for one event day on one relative orbit, compared with the same orbit's baseline."""
    day_start = ee.Date(date)
    day_end = day_start.advance(1, "day")
    same_orbit = ee.Filter.eq("relativeOrbitNumber_start", orbit)

    event = s1_collection(aoi, day_start, day_end).filter(same_orbit).mosaic()
    baseline = s1_collection(aoi, *pkg["baseline"]).filter(same_orbit).median()

    after = smooth_vv(event, p["smooth_m"])
    before = smooth_vv(baseline, p["smooth_m"])

    flood = after.subtract(before).lt(p["diff_db"]).And(after.lt(p["water_db"]))

    permanent = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence").unmask(0)
    slope = ee.Terrain.slope(ee.Image("USGS/SRTMGL1_003"))
    flood = flood.And(permanent.lt(p["perm_water_pct"])).And(slope.lt(p["max_slope_deg"]))

    connected = flood.selfMask().connectedPixelCount(25, True)
    return flood.updateMask(connected.gte(p["min_pixels"])).selfMask().clip(aoi).rename("flood")


def flooded_km2(mask, aoi, scale):
    area = mask.multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=aoi, scale=scale, maxPixels=1e10
    )
    return ee.Number(area.get("flood")).divide(1e6)


def to_polygons(mask, aoi, props, scale):
    vectors = mask.reduceToVectors(
        geometry=aoi, scale=scale, geometryType="polygon",
        eightConnected=True, labelProperty="flood", maxPixels=1e10,
    )

    def tidy(f):
        f = ee.Feature(f).simplify(SIMPLIFY_M)
        return f.set({"area_m2": f.geometry().area(1), **props})

    return vectors.map(tidy).filter(ee.Filter.gte("area_m2", MIN_POLYGON_M2))


def event_scenes(aoi, pkg):
    """(date, orbit) pairs that have both an event scene and a baseline on the same orbit."""
    rows = scene_rows(s1_collection(aoi, *pkg["event"]))
    base_orbits = {r["orbit"] for r in scene_rows(s1_collection(aoi, *pkg["baseline"]))}
    pairs = sorted({(r["time"][:10], r["orbit"]) for r in rows if r["orbit"] in base_orbits})
    return pairs


def write_geojson(fc_info, path, meta):
    fc_info["reachpoint"] = meta  # GeoJSON foreign member; ignored by map libraries
    path.write_text(json.dumps(fc_info, separators=(",", ":")))
    return path.stat().st_size


def cmd_detect(args, pkg, aoi):
    p = {**DEFAULTS, **{k: v for k, v in vars(args).items() if k in DEFAULTS and v is not None}}
    pairs = event_scenes(aoi, pkg)
    if args.date:
        pairs = [x for x in pairs if x[0] in args.date]
    if not pairs:
        sys.exit("No event scene with a matching baseline orbit. Run `list` and check the windows.")

    out_dir = DATA_DIR / args.package
    out_dir.mkdir(parents=True, exist_ok=True)
    year = pkg["event"][0][:4]
    masks, per_date = [], []

    for date, orbit in pairs:
        mask = flood_for_date(aoi, pkg, date, orbit, p)
        masks.append(mask)
        km2 = flooded_km2(mask, aoi, p["scale_m"]).getInfo()
        per_date.append({"date": date, "orbit": orbit, "flooded_km2": round(km2, 2)})
        print(f"  {date} orbit {orbit}: {km2:.2f} km² flooded (detected)")
        if args.per_date:
            props = {"package": args.package, "acquired": date, "orbit": orbit, "kind": "observed_extent"}
            info = to_polygons(mask, aoi, props, p["scale_m"]).getInfo()
            path = out_dir / f"extent-{date}-o{orbit}.geojson"
            size = write_geojson(info, path, {"label": LABEL.format(dates=date), "attribution": ATTRIBUTION.format(year=year)})
            print(f"    -> {path.relative_to(DATA_DIR.parent)} ({size / 1024:.0f} KB)")

    dates = sorted({d for d, _ in pairs})
    max_extent = ee.ImageCollection(masks).max().rename("flood")
    props = {"package": args.package, "acquired": ",".join(dates), "kind": "max_observed_extent"}
    info = to_polygons(max_extent, aoi, props, p["scale_m"]).getInfo()
    meta = {
        "label": LABEL.format(dates=", ".join(dates)),
        "attribution": ATTRIBUTION.format(year=year),
        "method": "Sentinel-1 VV change detection vs same-orbit baseline median",
        "parameters": p,
        "baseline_window": pkg["baseline"],
        "scenes": per_date,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    path = out_dir / "extent.geojson"
    size = write_geojson(info, path, meta)
    total = flooded_km2(max_extent, aoi, p["scale_m"]).getInfo()
    summary = {**meta, "flooded_km2_max": round(total, 2), "polygons": len(info["features"]), "bytes": size}
    (out_dir / "run-summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    print(f"Max extent over {len(dates)} dates: {total:.2f} km², {len(info['features'])} polygons")
    print(f"-> {path.relative_to(DATA_DIR.parent)} ({size / 1024:.0f} KB). Next: python data/scripts/check_extent_budget.py {path.relative_to(DATA_DIR.parent)}")


def cmd_compare(args, pkg, aoi):
    ours_path = DATA_DIR / args.package / "extent.geojson"
    def load(path):
        return ee.FeatureCollection([ee.Feature(f) for f in json.loads(Path(path).read_text())["features"]])

    ours, ref = load(ours_path), load(args.reference)
    scale = DEFAULTS["scale_m"]

    def mask(fc):
        return ee.Image(0).byte().paint(fc, 1).clip(aoi).rename("flood")

    a, b = mask(ours), mask(ref)
    stats = {
        "ours_km2": flooded_km2(a.selfMask(), aoi, scale),
        "reference_km2": flooded_km2(b.selfMask(), aoi, scale),
        "overlap_km2": flooded_km2(a.And(b).selfMask(), aoi, scale),
        "union_km2": flooded_km2(a.Or(b).selfMask(), aoi, scale),
    }
    s = {k: round(v.getInfo(), 2) for k, v in stats.items()}
    iou = s["overlap_km2"] / s["union_km2"] if s["union_km2"] else 0
    ref_found = s["overlap_km2"] / s["reference_km2"] if s["reference_km2"] else 0
    print(json.dumps(s, indent=2))
    print(f"IoU {iou:.2f} · share of reference we detected {ref_found:.0%}")
    print("Read it with the urban caveat: low agreement in the city core is expected for Sentinel-1.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("step", choices=["list", "detect", "compare"])
    parser.add_argument("--project", required=True, help="Google Cloud project registered for Earth Engine")
    parser.add_argument("--package", default="hy-2025-11", choices=sorted(PACKAGES))
    parser.add_argument("--date", action="append", help="detect: only this event date (YYYY-MM-DD); repeatable")
    parser.add_argument("--per-date", action="store_true", help="detect: also write one GeoJSON per date")
    parser.add_argument("--reference", help="compare: published flood map as GeoJSON")
    for key, value in DEFAULTS.items():
        parser.add_argument(f"--{key.replace('_', '-')}", dest=key, type=type(value), help=f"default {value}")
    args = parser.parse_args()

    ee.Initialize(project=args.project)
    pkg = PACKAGES[args.package]
    aoi = ee.Geometry.Rectangle(pkg["bbox"])
    {"list": cmd_list, "detect": cmd_detect, "compare": cmd_compare}[args.step](args, pkg, aoi)


if __name__ == "__main__":
    main()
