"""Every street (including sois) in Hat Yai city, for the v2 neighbour directions: which way a house faces.

    python data/scripts/fetch_v2_streets.py

Writes data/hy-2025-11/v2-streets.geojson from OpenStreetMap (ODbL) through the Overpass API.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx

PKG = Path(__file__).resolve().parents[1] / "hy-2025-11"
BBOX = (6.9873, 100.4288, 7.0483, 100.5062)  # area P-B: south, west, north, east
KINDS = "residential|living_street|unclassified|service|tertiary|secondary|primary|trunk|pedestrian|footway"
QUERY = f"""[out:json][timeout:120];
way["highway"~"^({KINDS})$"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
out geom;"""
ENDPOINTS = ["https://maps.mail.ru/osm/tools/overpass/api/interpreter", "https://overpass.private.coffee/api/interpreter",
             "https://overpass-api.de/api/interpreter"]


def main() -> None:
    data = None
    for url in ENDPOINTS:
        try:
            r = httpx.post(url, data={"data": QUERY}, timeout=180, headers={"User-Agent": "ReachPoint hackathon prototype"})
            r.raise_for_status()
            data = r.json()
            break
        except Exception as e:  # try the next mirror
            print(url, "failed:", e)
    if data is None:
        raise SystemExit("Overpass unavailable")
    feats = []
    for w in data["elements"]:
        if w.get("type") != "way" or len(w.get("geometry", [])) < 2:
            continue
        t = w.get("tags", {})
        feats.append({"type": "Feature", "properties": {"id": w["id"], "kind": t.get("highway"), "name": t.get("name"), "nameTh": t.get("name:th"), "nameEn": t.get("name:en")},
                      "geometry": {"type": "LineString",
                                   "coordinates": [[round(p["lon"], 6), round(p["lat"], 6)] for p in w["geometry"]]}})
    out = {"type": "FeatureCollection", "source": "OpenStreetMap contributors (ODbL), via Overpass", "features": feats}
    (PKG / "v2-streets.geojson").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print(len(feats), "streets")


if __name__ == "__main__":
    main()
