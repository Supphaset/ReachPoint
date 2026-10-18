# Flood data packages

V2 uses the cached inputs and `v2-*` outputs in `hy-2025-11/`; see the
[v2 code map](../docs/planning/v2-code-map.md). Classic surge/briefing generators are retired.
The geography catalogue remains an offline preparation/test dependency.

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

## V2 preparation and rebuilds

The app runs from the committed Hat Yai package. Do not rebuild it just to start the demo: rebuilding can
change the scenario, cached readings and evaluation results. Inputs retain their sources in [SOURCES.md](SOURCES.md).

Preparation uses both the API dependencies and `data/requirements.txt`; Earth Engine exports additionally
require an authenticated, authorized sandbox project. No Earth Engine request runs in the app.

| Order | Tool | Inputs / output |
|---|---|---|
| 1 | `scripts/build_v2_buildings.py --project YOUR_SANDBOX_PROJECT`, `scripts/fetch_v2_streets.py` | Export Open Buildings and fetch OSM streets; writes `v2-buildings.json.gz` and `v2-streets.geojson` |
| 2 | `scripts/build_v2_zoning.py` | Buildings, streets and retained baseline zones; writes v2 zones, blocks, sectors and building assignments |
| 3 | `scripts/build_v2_terrain.py --project YOUR_SANDBOX_PROJECT`, `scripts/build_v2_basin.py --project YOUR_SANDBOX_PROJECT`, `scripts/build_v2_basin_rain.py --project YOUR_SANDBOX_PROJECT` | Export city terrain, basin terrain/land cover and basin rainfall; cached OSM basin channels and gauge readings are also required |
| 4 | `scripts/build_v2_basin_sim.py` | Runs the basin model into ignored `data/.cache/`; arguments control resolution, rain, inflow, drainage and terrain corrections |
| 5 | `scripts/publish_v2_sim.py RUN` | Reads `data/.cache/v2-basin-sim-RUN.*`; downsamples the water surface to city terrain and writes `v2-sim.json` / `v2-sim.bin.gz` |
| 6 | `scripts/build_v2_rain_response.py`, `scripts/build_v2_shelters.py` | Build extra-rain response and candidate-shelter outputs from published simulation data and their other cached inputs |
| 7 | `scripts/build_v2_scenario.py` | Writes synthetic messages/households/plans and evaluation truth; uses an independent `data/.cache/v2-truth-sim.*` run if available, otherwise the published model |
| 8 | `api/scripts/v2_batch_read.py` (from the repository root) | Optionally reads the scenario with Gemini into `v2-facts.json`; requires configured credentials and authorized model usage |
| 9 | `python -m api.v2.board`, `python api/scripts/eval_v2.py` | Refreshes timeline and evaluation; evaluation writes `docs/eval/v2-results.md` |

Paths beginning `scripts/` in this table are relative to `data/`; invoke them as
`python data/scripts/…` from the repository root. These are preparation steps, not one shell command.
Follow each script's arguments and input paths; the table is not a claim that defaults reproduce the submitted run.

The committed model metadata identifies run `s10` at 75 m with rain factor 1.6, inflow 0.35, urban Manning
coefficient 0.12, drainage 5 mm/h, urban ground correction 1 m, street-ground correction enabled and channel-width
exponent 0.3. The generator defaults differ. Publishing requires a named cached run; source `.cache` runs and
independent truth runs are not committed. The rain-response builder additionally needs a published extra-60-mm
run under `data/.cache/v2-sim-rain60.*`. Preserve the committed outputs unless intentionally regenerating them.

The older diffusive city-only generator is retired; `publish_v2_sim.py` is the current publication step.
Satellite extent is used separately as dated comparison context, not as depth input to the basin simulation.

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

## People per segment (D27, D31)

Earth Engine counts people in each segment two ways (WorldPop, and Open Buildings × people per building from DOPA's registered population) and writes `exposure.json`. Run it after the segments change, then rebuild the geography so every segment and zone gets an `estimate`:

```bash
python data/ee/flood_check.py exposure --project YOUR_SANDBOX_PROJECT --package hy-2025-11
python data/scripts/build_geography.py hy-2025-11
```

Each estimate is a range, rounded outwards: `everyone` living there, `inSatelliteExtent` (inside the 24 Nov extent), and, for city segments that are mostly "no satellite data", `modelledFlooded`: where reported depths plus ground height put water (D31, labelled as a model). It is never a count of victims and never adds to reviewed counts. The district sanity check against GISTDA is recorded in `SOURCES.md`.

## Tests

```bash
python3 -m unittest discover -s data/tests -v
```
