"""Check a flood extent GeoJSON against the package rules (eng review R11, connection C1).

    python data/scripts/check_extent_budget.py data/hy-2025-11/extent.geojson

Fails (exit 1) if the file is over 300 KB, isn't a valid FeatureCollection of
polygons, falls outside its package AOI, has polygons under 0.5 ha, or is
missing the label, attribution and acquisition dates. Uses only the standard library.
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages import MAX_BYTES, MIN_POLYGON_M2, PACKAGES  # noqa: E402

EARTH_R = 6_371_008.8
AREA_TOLERANCE = 0.9  # simplification after the EE area filter can shrink a polygon a little


def ring_area_m2(ring):
    """Approximate area of a lon/lat ring (equirectangular projection at the ring's mean latitude)."""
    lat0 = math.radians(sum(pt[1] for pt in ring) / len(ring))
    xs = [math.radians(pt[0]) * EARTH_R * math.cos(lat0) for pt in ring]
    ys = [math.radians(pt[1]) * EARTH_R for pt in ring]
    return abs(sum(xs[i] * ys[i + 1] - xs[i + 1] * ys[i] for i in range(len(ring) - 1))) / 2


def polygon_area_m2(rings):
    return ring_area_m2(rings[0]) - sum(ring_area_m2(r) for r in rings[1:])


def polygons_of(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return geom["coordinates"]
    return None


def check(path):
    path = Path(path)
    errors = []
    size = path.stat().st_size
    if size > MAX_BYTES:
        errors.append(f"file is {size / 1024:.0f} KB, budget is {MAX_BYTES // 1024} KB")

    try:
        doc = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return [f"not valid JSON: {exc}"], {}

    if doc.get("type") != "FeatureCollection" or not isinstance(doc.get("features"), list):
        return errors + ["not a GeoJSON FeatureCollection"], {}

    meta = doc.get("reachpoint", {})
    for key in ("label", "attribution"):
        if not meta.get(key):
            errors.append(f"missing reachpoint.{key}")

    package = None
    total_m2, small = 0.0, 0
    for i, feat in enumerate(doc["features"]):
        props = feat.get("properties") or {}
        package = package or props.get("package")
        if not props.get("acquired"):
            errors.append(f"feature {i}: missing 'acquired' date")
        polys = polygons_of(feat.get("geometry") or {})
        if polys is None:
            errors.append(f"feature {i}: geometry is not a polygon")
            continue
        for rings in polys:
            if any(len(r) < 4 or r[0] != r[-1] for r in rings):
                errors.append(f"feature {i}: ring not closed or too short")
                continue
            area = polygon_area_m2(rings)
            total_m2 += area
            if area < MIN_POLYGON_M2 * AREA_TOLERANCE:
                small += 1

    if small:
        errors.append(f"{small} polygon(s) under {MIN_POLYGON_M2 / 10_000:g} ha")

    bbox = PACKAGES.get(package, {}).get("bbox")
    if package and not bbox:
        errors.append(f"unknown package '{package}'")
    if bbox:
        west, south, east, north = bbox
        eps = 1e-6
        outside = [
            i for i, f in enumerate(doc["features"])
            for rings in (polygons_of(f.get("geometry") or {}) or [])
            for ring in rings for lon, lat, *_ in ring
            if not (west - eps <= lon <= east + eps and south - eps <= lat <= north + eps)
        ]
        if outside:
            errors.append(f"{len(set(outside))} feature(s) extend outside the {package} AOI")

    summary = {"package": package, "features": len(doc["features"]), "kb": round(size / 1024, 1),
               "flooded_km2_approx": round(total_m2 / 1e6, 2)}
    return errors, summary


def main(argv):
    if len(argv) != 2:
        sys.exit(__doc__)
    errors, summary = check(argv[1])
    print(json.dumps(summary))
    for e in errors:
        print(f"FAIL: {e}")
    if errors:
        sys.exit(1)
    print("OK: within budget and package rules")


if __name__ == "__main__":
    main(sys.argv)
