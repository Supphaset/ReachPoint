# Flood data packages

Owner: user (volunteer workspace and flood map). This is connection **C1** in the [integration map](../docs/collaboration/integration-map.md).

Each package folder holds what the app shows for one past flood event:

| Path | What |
|---|---|
| `packages.py` | Package AOIs, date windows and export rules |
| `ee/flood_check.py` | Earth Engine Sentinel-1 flood check: `list`, `detect`, `compare` |
| `scripts/check_extent_budget.py` | Size and rule check for an extent file (no Earth Engine needed) |
| `<package>/scenes.csv` | Sentinel-1 scenes found for the baseline and event windows |
| `<package>/extent-<date>-o<orbit>.geojson` | One dated Sentinel-1 pass, ≤ 300 KB, with label and attribution |
| `<package>/extent-max-observed.geojson` | Union of all passes, for reference and comparison only (not shown in the app) |
| `<package>/layers.json` | Which layers the app shows, their labels and the default |
| `<package>/reported-flooding.geojson` | Cited reports of flooding the satellite can't see (city centre) |
| `<package>/no-satellite-data.geojson` | Dense built-up area where Sentinel-1 can't see street water: shown as "no satellite data", never as dry (D26) |
| `<package>/geography-source.json` | **Hand-drawn** zones and landmarks (edit this one) |
| `<package>/areas.geojson`, `zones.geojson`, `segments.geojson`, `landmarks.geojson` | Built from the source: areas → zones → one segment per landmark, plus D1 |
| `scripts/build_geography.py` | Builds the four files above, `districts.geojson`, and the C1 fixture `contract/fixtures/areas.<package>.json` |
| `scripts/cut_city_zones.py` | Cuts the city (P-B) into zones and segments along OSM streets, grouped by the city's 4 districts (D30); writes the P-B zones into `geography-source.json` |
| `<package>/osm-lines.geojson`, `osm-municipality.geojson` | Cached OpenStreetMap roads, railway, river, canals and the municipal boundary (ODbL) |
| `<package>/run-summary.json` | Parameters, scenes used and flooded area for the run |
| `SOURCES.md` | Record of every run and its comparison with published maps |

## One-time setup (your sandbox project)

1. In the Google Cloud console, create or pick your **sandbox** project. Register it for Earth Engine as **noncommercial** (Community tier) at <https://code.earthengine.google.com/register>.
2. Install the client and sign in:

```bash
python3 -m pip install -r data/requirements.txt
```

```bash
earthengine authenticate
```

## Monday flood check (about 2 hours)

1. List the scenes. Check that 23 Nov 2025 is there, and look for 24–25 Nov:

```bash
python data/ee/flood_check.py list --project YOUR_SANDBOX_PROJECT --package hy-2025-11
```

2. Detect the flood extent (also writes one file per date):

```bash
python data/ee/flood_check.py detect --project YOUR_SANDBOX_PROJECT --package hy-2025-11 --per-date
```

3. Check it against the package rules:

```bash
python data/scripts/check_extent_budget.py data/hy-2025-11/extent-2025-11-23-o164.geojson
```

4. Compare it with a published map. Download the EOS or AIT Hat Yai shapefile from [Sentinel Asia](https://sentinel-asia.org/EO/2025/article20251119TH.html) and convert it to GeoJSON (for example in QGIS). Then run:

```bash
python data/ee/flood_check.py compare --project YOUR_SANDBOX_PROJECT --package hy-2025-11 --reference path/to/eos-hatyai.geojson
```

   Simplify a large reference map first (for example to 15 m in QGIS); Earth Engine rejects requests over about 10 MB.

5. Record the result in `SOURCES.md`: scenes, parameters, flooded km², IoU, and what looks wrong. Don't commit the reference map itself until its licence is checked.

**If the file is over 300 KB**, rerun `detect` with a larger `--min-pixels` (e.g. 16) or `--scale-m 30`.

**If the city core shows no water**, that's the expected Sentinel-1 urban limit. Keep the legend text and don't tune thresholds to force it.

**If our extent is clearly wrong**, use the fallback in pack §5.1c: the published polygons, with attribution, after checking their licence.

## Zones, segments and landmarks

**City (P-B, D30):** zones and segments are cut along real roads, the railway, the river and canals, and each zone sits inside one of the city's 4 districts (เขต 1–4). IDs are generic (`B-3-L5`, shown as "B-3 · L5 School"); landmarks are generic types, not real buildings. **Rural (P-A, P-C):** zones are hand-drawn and cut into one segment per landmark (the part nearer that landmark than any other).

1. Refresh the "no satellite data" mask (Earth Engine, only when its parameters change):

```bash
python data/ee/flood_check.py nodata --project YOUR_SANDBOX_PROJECT --package hy-2025-11
```

2. Re-cut the city zones (only when the cut rules change). The district outlines file is traced from the city's community map and kept outside the repo; see `SOURCES.md`:

```bash
python data/scripts/cut_city_zones.py --districts path/to/districts-traced.geojson
```

3. After editing `geography-source.json`, rebuild and test:

```bash
python data/scripts/build_geography.py hy-2025-11
```

## Tests

```bash
python3 -m unittest discover -s data/tests -v
```
