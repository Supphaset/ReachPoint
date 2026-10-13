"""Resolve a caller's location (D25): a pin (GPS or map tap) or an address, snapped to segment and landmark.

The exact point is kept for the coordinator and the team that takes the job only; shared views use the landmark.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache

from api.location import geo, pinpoint
from api.views.store import ROOT

ADDRESSES = ROOT / "contract" / "seed" / "addresses.synthetic.json"
LANDMARK_WORDS = {
    "School": ("school", "โรงเรียน"), "Temple": ("temple", "วัด"), "Market": ("market", "ตลาด"),
    "Mosque": ("mosque", "มัสยิด"), "Shrine": ("shrine", "ศาลเจ้า"),
    "Health centre": ("health centre", "health center", "clinic", "อนามัย", "รพ.สต."),
    "Community building": ("community", "ชุมชน", "ศาลา"),
}


@lru_cache(maxsize=1)
def _addresses() -> tuple:
    return tuple(json.loads(ADDRESSES.read_text())["addresses"])


def _norm(s: str) -> str:
    return re.sub(r"[\s,.]+", "", s.lower())


def _standin(text: str) -> dict | None:
    """No Pinpoint key: the made-up demo addresses, then a zone code plus a landmark kind ("B-3 … ตลาด")."""
    n = _norm(text)
    for a in _addresses():
        if _norm(a["address"]) in n or _norm(a["addressEn"]) in n:
            return {"at": a["at"], "precision": a["precision"], "label": a["address"]}
    low = text.lower()
    kinds = [k for k, words in LANDMARK_WORDS.items() if any(w in low for w in words)]
    for prefix, num in re.findall(r"\b([ABC])\s*-?\s*(\d{1,2})\b", text.upper()):
        zid = f"{prefix}-{int(num)}"
        for f in geo._layer("landmarks"):
            p = f["properties"]
            if p.get("zoneId") == zid and any(p["label"].endswith(k) for k in kinds):
                return {"at": f["geometry"]["coordinates"], "precision": "landmark", "label": p["label"]}
    return None


def _snap(lon: float, lat: float, base: dict) -> dict:
    area = geo.area_of(lon, lat)
    if area is None:
        return {**base, "status": "outside_area", "at": None}  # never keep a point outside the demo area
    seg = geo.segment_of(lon, lat)
    lm = geo.nearest_landmark(lon, lat, area["id"]) if seg is None else next(
        (f["properties"] for f in geo._layer("landmarks") if f["properties"]["id"] == seg.get("landmarkId")), None) or geo.nearest_landmark(lon, lat, area["id"])
    return {**base, "status": "located", "at": [round(lon, 6), round(lat, 6)], "areaId": area["id"],
            "zoneId": lm.get("zoneId"), "segmentId": lm["segmentId"], "landmarkId": lm["id"], "landmarkLabel": lm["label"]}


def resolve(loc: dict | None) -> dict | None:
    """LocationInput → Location (contract/api.md, "Locating a request")."""
    if not loc:
        return None
    if loc.get("kind") == "pin":
        lat, lon = float(loc["lat"]), float(loc["lon"])
        method = loc.get("method") if loc.get("method") in {"gps", "pinpoint"} else "map"
        acc = loc.get("accuracyM")
        base = {"kind": "pin", "method": method, "provider": "pinpoint" if method == "pinpoint" else "device",
                "precision": "house" if method == "gps" and acc is not None and acc <= 30 else "street" if method == "gps" else "street",
                "source": "caller-selected Pinpoint match" if method == "pinpoint" else "caller pin (GPS)" if method == "gps" else "caller pin (map)",
                **({"accuracyM": round(float(acc))} if acc is not None else {})}
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return {**base, "status": "unlocated", "at": None, "precision": None}
        return _snap(lon, lat, base)
    if loc.get("kind") == "address":
        text = str(loc.get("text") or "").strip()[:300]
        base = {"kind": "address", "method": "address", "address": text}
        if not text:
            return {**base, "status": "unlocated", "at": None, "precision": None, "provider": "stand-in", "source": "address not found"}
        hit, provider = pinpoint.geocode(text), "pinpoint"
        if hit is None:
            hit, provider = _standin(text), "stand-in"
        if hit is None:
            return {**base, "status": "unlocated", "at": None, "precision": None, "provider": provider, "source": "address not found"}
        source = {"house": "Pinpoint address match", "street": "Pinpoint: street level", "area": "Pinpoint: area only",
                  "landmark": "landmark named in the address"}[hit["precision"]]
        if provider == "stand-in" and hit["precision"] != "landmark":
            source = "demo address list (Pinpoint stand-in)"
        return _snap(hit["at"][0], hit["at"][1], {**base, "provider": provider, "precision": hit["precision"],
                                                   "source": source, "matched": hit["label"]})
    return None


def exact_pickup(location: dict | None) -> dict | None:
    """The approved case's exact pickup point from a located Location (D25), else None."""
    if not location or location.get("status") != "located":
        return None
    return {"at": location["at"], "precision": location["precision"], "source": location["source"]}
