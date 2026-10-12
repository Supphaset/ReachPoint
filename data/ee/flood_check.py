"""Sentinel-1 flood check for ReachPoint (pack §5.1c).

Three steps, run from the repo root with your sandbox Google Cloud project:

    python data/ee/flood_check.py list    --project YOUR_EE_PROJECT --package hy-2025-11
    python data/ee/flood_check.py detect  --project YOUR_EE_PROJECT --package hy-2025-11
    python data/ee/flood_check.py compare --project YOUR_EE_PROJECT --package hy-2025-11 \
        --reference path/to/eos-hatyai.geojson
    python data/ee/flood_check.py nodata  --project YOUR_EE_PROJECT --package hy-2025-11

`list` writes the available scenes, `detect` writes one flood extent GeoJSON per pass (plus a max-observed union for reference),
`compare` measures agreement with a published map, `nodata` writes the dense built-up area where
Sentinel-1 can't see street water (shown as "no satellite data", never as dry; D26). Nothing here runs in the app;
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
    "close_m": 30,          # morphological closing: fills dry gaps and smooths edges under ~this size
    "scale_m": 30,          # vectorisation scale (run 1: 20 m was over budget)
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
    if p["close_m"]:
        r = p["close_m"]
        flood = flood.unmask(0).focalMax(r, "circle", "meters").focalMin(r, "circle", "meters")

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
        f = ee.Feature(f).simplify(SIMPLIFY_M).intersection(aoi, 1)
        return f.set({"area_m2": f.geometry().area(1), **props})

    return vectors.map(tidy).filter(ee.Filter.gte("area_m2", MIN_POLYGON_M2))


def event_scenes(aoi, pkg):
    """(date, orbit) pairs that have both an event scene and a baseline on the same orbit."""
    rows = scene_rows(s1_collection(aoi, *pkg["event"]))
    base_orbits = {r["orbit"] for r in scene_rows(s1_collection(aoi, *pkg["baseline"]))}
    first_time = {}
    for r in rows:
        if r["orbit"] in base_orbits:
            first_time.setdefault((r["time"][:10], r["orbit"]), r["time"])
    return [(d, o, first_time[(d, o)]) for d, o in sorted(first_time)]


KEEP_PROPS = ("package", "acquired", "orbit", "kind", "area_m2")
BANGKOK = timezone(timedelta(hours=7))


def local_time(utc_text):
    """'2025-11-23T23:03' (UTC) -> '2025-11-24 06:03 Bangkok'."""
    t = datetime.strptime(utc_text, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc).astimezone(BANGKOK)
    return t.strftime("%Y-%m-%d %H:%M") + " Bangkok"


def round_coords(c):
    # 4 dp is about 11 m: below the 40 m simplification, so no visible change, and ~15% smaller files.
    return [round_coords(x) for x in c] if isinstance(c[0], list) else [round(c[0], 4), round(c[1], 4)]


def drop_small_parts(geom):
    """reduceToVectors joins pixels that touch at a corner into one multipart polygon;
    drop parts under the minimum area so lone pixels don't survive the area filter."""
    sys.path.insert(0, str(DATA_DIR / "scripts"))
    from check_extent_budget import polygon_area_m2

    parts = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    keep = [p for p in parts if polygon_area_m2(p) >= MIN_POLYGON_M2]
    if not keep:
        return None
    return {"type": "Polygon", "coordinates": keep[0]} if len(keep) == 1 else {"type": "MultiPolygon", "coordinates": keep}


def write_geojson(fc_info, path, meta):
    kept = []
    for f in fc_info["features"]:
        if f["geometry"]["type"] not in ("Polygon", "MultiPolygon"):
            continue
        f["geometry"]["coordinates"] = round_coords(f["geometry"]["coordinates"])  # round first, then measure
        geom = drop_small_parts(f["geometry"])
        if geom is None:
            continue
        f["geometry"] = geom
        kept.append(f)
    fc_info["features"] = kept
    for f in fc_info["features"]:
        f.pop("id", None)
        props = {k: v for k, v in f["properties"].items() if k in KEEP_PROPS}
        props["area_m2"] = round(props.get("area_m2", 0))
        f["properties"] = props
    fc_info.pop("columns", None)
    fc_info["reachpoint"] = meta  # GeoJSON foreign member; ignored by map libraries
    path.write_text(json.dumps(fc_info, separators=(",", ":")))
    return path.stat().st_size


def cmd_detect(args, pkg, aoi):
    p = {**DEFAULTS, **{k: v for k, v in vars(args).items() if k in DEFAULTS and v is not None}}
    pairs = event_scenes(aoi, pkg)
    if args.date:
        pairs = [x for x in pairs if x[0] in args.date]
    global SIMPLIFY_M
    SIMPLIFY_M = args.simplify_m
    if not pairs:
        sys.exit("No event scene with a matching baseline orbit. Run `list` and check the windows.")

    out_dir = DATA_DIR / args.package
    out_dir.mkdir(parents=True, exist_ok=True)
    year = pkg["event"][0][:4]
    masks, per_date = [], []

    for date, orbit, utc in pairs:
        mask = flood_for_date(aoi, pkg, date, orbit, p)
        masks.append(mask)
        km2 = flooded_km2(mask, aoi, p["scale_m"]).getInfo()
        local = local_time(utc)
        per_date.append({"date_utc": date, "acquired_utc": utc, "acquired_local": local, "orbit": orbit, "flooded_km2": round(km2, 2)})
        print(f"  {local} (UTC {utc}) orbit {orbit}: {km2:.2f} km² flooded (detected)")
        if args.per_date:
            props = {"package": args.package, "acquired": local, "orbit": orbit, "kind": "observed_extent"}
            info = to_polygons(mask, aoi, props, p["scale_m"]).getInfo()
            path = out_dir / f"extent-{date}-o{orbit}.geojson"
            size = write_geojson(info, path, {"label": LABEL.format(dates=local), "attribution": ATTRIBUTION.format(year=year)})
            print(f"    -> {path.relative_to(DATA_DIR.parent)} ({size / 1024:.0f} KB)")

    dates = [s["acquired_local"] for s in per_date]
    # Union of all passes. ImageCollection.max() gave a smaller, wrong area here, so OR them explicitly.
    union = masks[0].unmask(0)
    for m in masks[1:]:
        union = union.Or(m.unmask(0))
    max_extent = union.selfMask().clip(aoi).rename("flood")
    props = {"package": args.package, "acquired": "; ".join(dates), "kind": "max_observed_extent"}
    info = to_polygons(max_extent, aoi, props, p["scale_m"]).getInfo()
    meta = {
        "label": LABEL.format(dates=", ".join(dates)),
        "attribution": ATTRIBUTION.format(year=year),
        "method": "Sentinel-1 VV change detection vs same-orbit baseline median",
        "parameters": {**p, "simplify_m": SIMPLIFY_M, "min_polygon_m2": MIN_POLYGON_M2},
        "baseline_window": pkg["baseline"],
        "scenes": per_date,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    path = out_dir / "extent-max-observed.geojson"  # reference only; the app shows one dated pass (layers.json)
    size = write_geojson(info, path, meta)
    total = flooded_km2(max_extent, aoi, p["scale_m"]).getInfo()
    summary = {**meta, "flooded_km2_max": round(total, 2), "polygons": len(info["features"]), "bytes": size}
    (out_dir / "run-summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    print(f"Max extent over {len(dates)} passes: {total:.2f} km², {len(info['features'])} polygons")
    print(f"-> {path.relative_to(DATA_DIR.parent)} ({size / 1024:.0f} KB). Next: python data/scripts/check_extent_budget.py {path.relative_to(DATA_DIR.parent)}")


def cmd_compare(args, pkg, aoi):
    ours_path = DATA_DIR / args.package / (args.ours or "extent-max-observed.geojson")
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


# "No satellite data" mask (D26), like the Copernicus GFM exclusion mask: dense built-up land, where
# radar double-bounce hides street water. Run 2026-10-12: 16 of 17 reported flood points fall inside it.
NODATA = {
    "built_class": 50,          # ESA WorldCover v200 "Built-up"
    "radius_m": 200,            # neighbourhood for the built-up share
    "min_share": 0.5,           # at least half the neighbourhood is built-up
    "min_area_m2": 300_000,     # drop small villages and isolated blocks
    "scale_m": 30,
}
NODATA_LABEL = ("No satellite data: dense built-up area where Sentinel-1 can't see street water. "
                "Flooding here is known only from reports and callers. Never shown as dry.")


def cmd_nodata(args, pkg, aoi):
    n = NODATA
    built = ee.ImageCollection("ESA/WorldCover/v200").first().select("Map").eq(n["built_class"])
    share = built.reduceNeighborhood(ee.Reducer.mean(), ee.Kernel.circle(n["radius_m"], "meters"))
    mask = share.gt(n["min_share"]).selfMask().reproject("EPSG:4326", None, n["scale_m"]).rename("flood")
    vectors = mask.reduceToVectors(geometry=aoi, scale=n["scale_m"], geometryType="polygon",
                                   eightConnected=True, labelProperty="flood", maxPixels=1e10)
    props = {"package": args.package, "kind": "no_satellite_data"}

    def tidy(f):
        f = ee.Feature(f)
        return f.simplify(n["scale_m"]).set({"area_m2": f.geometry().area(1), **props})

    info = vectors.map(tidy).filter(ee.Filter.gte("area_m2", n["min_area_m2"])).getInfo()
    meta = {
        "label": NODATA_LABEL,
        "attribution": "ESA WorldCover 10 m 2021 v200 (CC BY 4.0), processed by ReachPoint",
        "method": "Share of WorldCover built-up pixels within the radius, above the minimum share",
        "parameters": n,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    path = DATA_DIR / args.package / "no-satellite-data.geojson"
    size = write_geojson(info, path, meta)
    km2 = sum(f["properties"]["area_m2"] for f in info["features"]) / 1e6
    print(f"No satellite data: {len(info['features'])} polygons, {km2:.2f} km²")
    print(f"-> {path.relative_to(DATA_DIR.parent)} ({size / 1024:.0f} KB)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("step", choices=["list", "detect", "compare", "nodata"])
    parser.add_argument("--project", required=True, help="Google Cloud project registered for Earth Engine")
    parser.add_argument("--package", default="hy-2025-11", choices=sorted(PACKAGES))
    parser.add_argument("--date", action="append", help="detect: only this event date (YYYY-MM-DD); repeatable")
    parser.add_argument("--per-date", action="store_true", help="detect: also write one GeoJSON per date")
    parser.add_argument("--reference", help="compare: published flood map as GeoJSON")
    parser.add_argument("--ours", help="compare: our file in the package folder (default extent-max-observed.geojson)")
    parser.add_argument("--simplify-m", type=float, default=SIMPLIFY_M, help=f"detect: polygon simplification in metres (default {SIMPLIFY_M})")
    for key, value in DEFAULTS.items():
        parser.add_argument(f"--{key.replace('_', '-')}", dest=key, type=type(value), help=f"default {value}")
    args = parser.parse_args()

    ee.Initialize(project=args.project)
    pkg = PACKAGES[args.package]
    aoi = ee.Geometry.Rectangle(pkg["bbox"])
    {"list": cmd_list, "detect": cmd_detect, "compare": cmd_compare, "nodata": cmd_nodata}[args.step](args, pkg, aoi)


if __name__ == "__main__":
    main()
