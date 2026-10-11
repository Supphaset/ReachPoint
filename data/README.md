# Flood data packages

Owner: user (volunteer workspace and flood map). This is connection **C1** in the [integration map](../docs/collaboration/integration-map.md).

Each package folder holds what the app shows for one past flood event:

| Path | What |
|---|---|
| `packages.py` | Package AOIs, date windows and export rules |
| `ee/flood_check.py` | Earth Engine Sentinel-1 flood check: `list`, `detect`, `compare` |
| `scripts/check_extent_budget.py` | Size and rule check for an extent file (no Earth Engine needed) |
| `<package>/scenes.csv` | Sentinel-1 scenes found for the baseline and event windows |
| `<package>/extent.geojson` | Max observed flood extent, ≤ 300 KB, with label and attribution |
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
python data/scripts/check_extent_budget.py data/hy-2025-11/extent.geojson
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

## Tests

```bash
python3 -m unittest discover -s data/tests -v
```
