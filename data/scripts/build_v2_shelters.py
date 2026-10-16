"""Candidate shelters for the v2 demo: real public buildings from OpenStreetMap (schools, universities, temples,
mosques, community and government halls) inside the city window, kept only where the published flood model stays
under 10 cm all week at the building. Capacity is an estimate from the footprint (about 2 m² per person on one floor),
not an official figure. The official 2025 evacuation-centre list is not in the data, so the map says "candidate".

    python data/scripts/build_v2_shelters.py

Writes data/hy-2025-11/v2-shelters.json.
"""

from __future__ import annotations

import gzip
import json
import math
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.v2 import geo as G  # noqa: E402

PKG = ROOT / "data" / "hy-2025-11"
ENDPOINTS = ["https://maps.mail.ru/osm/tools/overpass/api/interpreter", "https://overpass.private.coffee/api/interpreter",
             "https://overpass-api.de/api/interpreter"]
KINDS = {"school": "School", "university": "University", "college": "College", "place_of_worship": "Temple or mosque",
         "community_centre": "Community hall", "townhall": "Town hall", "hospital": "Hospital"}


CACHE = ROOT / "data" / ".cache" / "v2-osm-amenities.json"


def fetch(bbox) -> list[dict]:
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    w, s, e, n = bbox
    q = f"""[out:json][timeout:60];
(nwr["amenity"~"^({'|'.join(KINDS)})$"]({s},{w},{n},{e}););
out center tags;"""
    for url in ENDPOINTS:
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": q}).encode(), headers={"User-Agent": "ReachPoint-hackathon/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                els = json.load(r)["elements"]
            CACHE.write_text(json.dumps(els))
            return els
        except Exception as ex:  # try the next mirror
            print("mirror failed:", url, ex)
    raise SystemExit("all Overpass mirrors failed")


def main() -> None:
    t = json.loads((PKG / "v2-terrain.json").read_text())
    meta = json.loads((PKG / "v2-sim.json").read_text())
    with gzip.open(PKG / "v2-sim.bin.gz", "rb") as fh:
        raw = fh.read()
    R, C, fb, step = meta["rows"], meta["cols"], meta["frameBytes"], meta["stepM"]
    w, s, e, n = meta["bbox"]
    geo = G.load()

    def max_depth(lon, lat):
        i, j = int((n - lat) / (n - s) * R), int((lon - w) / (e - w) * C)
        if not (0 <= i < R and 0 <= j < C):
            return None
        return max(raw[k * fb + i * C + j] for k in range(meta["hours"] + 1)) * step

    # real news reports of deep water: the model is too shallow in places, so these overrule it
    rep = {f["properties"]["id"]: f["geometry"]["coordinates"] for f in json.loads((PKG / "reported-flooding.geojson").read_text())["features"]}
    deep = [rep[k] for k, r in json.loads((PKG / "exposure.json").read_text())["reportedDepthM"].items() if r and r[1] >= 0.5 and k in rep]
    out = []
    for el in fetch(t["bbox"]):
        tags = el.get("tags", {})
        c = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
        if c.get("lat") is None:
            continue
        lon, lat = c["lon"], c["lat"]
        amen = tags.get("amenity")
        if amen == "hospital":
            continue  # hospitals are for patients; list them separately later if needed
        name = tags.get("name:th") or tags.get("name") or tags.get("name:en")
        if not name:
            continue
        d = max_depth(lon, lat)
        if d is None or d > 0.1:
            continue  # flooded at some point in the model week: not a safe shelter
        if any(math.hypot((lon - x) * 110_000, (lat - y) * 110_000) < 500 for x, y in deep):
            continue  # people reported deep water within 500 m in Nov 2025
        b = geo.snap(lon, lat, 60)
        area = b.area_m2 if b else 400
        zone = geo.zone_at(lon, lat)
        out.append({"id": f"S{len(out) + 1:02d}", "name": name, "nameEn": tags.get("name:en"), "kind": KINDS.get(amen, amen),
                    "lon": round(lon, 6), "lat": round(lat, 6), "zoneId": zone, "groundM": b.ground_m if b else None,
                    "capacity": int(max(60, min(800, area / 2))), "maxModelDepthM": round(d, 2), "osm": f"{el['type']}/{el['id']}"})
    # one shelter per place: buildings within ~350 m are the same campus; keep the name that is not a faculty or wing
    sub = ("คณะ", "ภาควิชา", "อาคาร", "ศูนย์", "สำนัก", "Faculty", "Department", "Building")
    out.sort(key=lambda x: (any(x["name"].startswith(p) for p in sub), x["kind"] not in ("University", "School", "College"), -x["capacity"]))
    kept = []
    for x in out:
        hit = next((k for k in kept if math.hypot((k["lon"] - x["lon"]) * 110_000, (k["lat"] - x["lat"]) * 110_000)
                    < (900 if "University" in (k["kind"], x["kind"]) else 350)), None)
        if hit:
            hit["capacity"] = min(3000, hit["capacity"] + x["capacity"] // 2)
            hit["buildings"] = hit.get("buildings", 1) + 1
        else:
            kept.append(x)
    out = kept[:20]
    for i, x in enumerate(out, 1):
        x["id"] = f"S{i:02d}"
    (PKG / "v2-shelters.json").write_text(json.dumps({
        "package": "hy-2025-11", "source": "OpenStreetMap public buildings (ODbL); dry all week in the published flood model",
        "note": "Candidate shelters for the demo, not the official 2025 evacuation-centre list. Capacity estimated from footprint.",
        "shelters": out}, ensure_ascii=False, indent=1))
    print(len(out), "shelters;", [(x["id"], x["name"], x["kind"], x["zoneId"], x["capacity"]) for x in out[:8]])


if __name__ == "__main__":
    main()
