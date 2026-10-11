"""Flood package definitions shared by the Earth Engine script and the budget check.

Bounding boxes are starting AOIs. Tighten them once the P-A/P-B/P-C and zone
boundaries are drawn (pack §5.1b). Coordinates are [west, south, east, north] in WGS 84.
"""

PACKAGES = {
    "hy-2025-11": {
        "name": "Hat Yai / Songkhla flood, Nov 2025",
        "bbox": [100.30, 6.85, 100.65, 7.15],
        # Baseline: before the event, same season. Event: the flood window (pack §5.1c).
        "baseline": ("2025-10-01", "2025-11-15"),
        "event": ("2025-11-19", "2025-12-05"),
        # Published maps to compare against (Sentinel Asia, 23 Nov 2025 pass).
        "references": ["EOS-RS flood proxy map v0.9", "AIT-VAP003-TH (Hat Yai District)"],
    },
    "bkk-2026-09": {
        "name": "Bangkok east flood, Sep 2026",
        "bbox": [100.65, 13.70, 100.95, 13.90],
        "baseline": ("2026-09-01", "2026-09-23"),
        "event": ("2026-09-24", "2026-10-05"),
        "references": [],
    },
}

# Export rules from eng review R11: drop polygons under 0.5 ha, simplify at ~15 m,
# one GeoJSON per package within 300 KB.
MIN_POLYGON_M2 = 5_000
SIMPLIFY_M = 15
MAX_BYTES = 300 * 1024

ATTRIBUTION = "Contains modified Copernicus Sentinel data {year}, processed by ReachPoint"
LABEL = (
    "Satellite extent computed by ReachPoint from Copernicus Sentinel-1 on {dates}; "
    "urban areas may be under-detected; households, teams, calls and quantities are synthetic."
)
