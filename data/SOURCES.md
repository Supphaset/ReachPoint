# Flood data sources and runs

Every published layer must trace back to an entry here. See pack §5.1b–c for why each source is used.

## Inputs

| Source | Use | Licence / attribution |
|---|---|---|
| Copernicus Sentinel-1 GRD (`COPERNICUS/S1_GRD`, Earth Engine) | Flood change detection | "Contains modified Copernicus Sentinel data {year}" |
| JRC Global Surface Water 1.4 (`JRC/GSW1_4/GlobalSurfaceWater`) | Mask permanent water | Pekel et al. 2016, EC JRC / Google |
| SRTM 30 m (`USGS/SRTMGL1_003`) | Mask slopes over 5° | NASA / USGS |
| Sentinel Asia products (EOS, AIT), 23 Nov 2025 | Comparison only; not redistributed until the licence is checked | As stated on each product |
| News and official reports (FM91, Bangkok Biz News, Thai PBS), 23–25 Nov 2025 | `reported-flooding.geojson`: the city centre, where Sentinel-1 can't see water | Cited per point; we paraphrase the text, not copy it |
| OpenStreetMap / Nominatim | Approximate locations for reported streets and landmarks | © OpenStreetMap contributors, ODbL |
| OpenStreetMap (Overpass, fetched 2026-10-12) | City zone and segment edges: trunk to tertiary roads, railway, river, canals; municipal boundary (relation 19981578) | © OpenStreetMap contributors, ODbL |
| Hat Yai City Municipality community map, "ผังรวม 103 ชุมชน" (updated 14 Nov 2565) | District (เขต 1–4) membership of each city zone. Not redistributed; only the traced district outlines were used, kept outside the repo | © เทศบาลนครหาดใหญ่; the map says it is approximate |
| ESA WorldCover 10 m 2021 v200 (`ESA/WorldCover/v200`) | "No satellite data" mask: dense built-up land (D26) | CC BY 4.0, © ESA WorldCover project |
| WorldPop Global 100 m, 2020 (`WorldPop/GP/100m/pop`) | People per segment, count 1 (D27) | CC BY 4.0, WorldPop (University of Southampton) |
| Google Open Buildings v3 polygons (`GOOGLE/Research/open-buildings/v3/polygons`), confidence ≥ 0.75 | People per segment, count 2: buildings × people per building (D27) | CC BY 4.0 and ODbL |
| DOPA registered population, อำเภอหาดใหญ่, 2567 (2024): 406,374 ([Wikipedia infobox](https://th.wikipedia.org/wiki/อำเภอหาดใหญ่), which links DOPA's district statistics; **to confirm** on stat.bora.dopa.go.th) | People per building for count 2: 406,374 / 149,430 buildings = 2.72 | Public statistics, กรมการปกครอง |
| FABDEM v1.2 bare-earth 30 m (`projects/sat-io/open-datasets/FABDEM`, community catalogue) | Ground height for the city flood model (D31) | CC BY-NC-SA 4.0 (noncommercial; fine for this prototype) |
| FAO GAUL 2025 level 2 (`FAO/GAUL/2025/level2`) | Hat Yai district outline for the GISTDA sanity check | FAO, non-commercial use |

## Runs

<!-- Copy one block per run. -->

### hy-2025-11: run 1 (2026-10-11)

- **Project:** `reachpoint-ee-sandbox` (Earth Engine noncommercial, Community tier).
- **Scenes:** 11 Sentinel-1 IW scenes (`hy-2025-11/scenes.csv`).
  - Baseline: 7 S1A scenes from 6 Oct to 11 Nov 2025, on orbits 164 (descending) and 70 (ascending).
  - Event passes used:

    | Bangkok time | UTC | Satellite | Orbit | Detected |
    |---|---|---|---|---|
    | 24 Nov 06:03 | 23 Nov 23:03 | S1A | 164 desc | 32.41 km² |
    | 29 Nov 18:35 | 29 Nov 11:35 | S1A | 70 asc | 24.10 km² |
    | 30 Nov 06:01 | 29 Nov 23:01 | S1C | 164 desc | 20.57 km² |

- **Parameters:**
  - Detection: VV diff < −3 dB and VV < −15 dB, 30 m focal median, 30 m closing.
  - Masks: slope < 5°, permanent water (JRC ≥ 80%), min 8 connected pixels.
  - Export: vectorised at 30 m, simplified at 40 m, parts under 0.5 ha dropped.
- **Outputs:**

  | File | Size | Budget check |
  |---|---|---|
  | `extent-2025-11-23-o164.geojson` (24 Nov pass) | 258 KB | passes |
  | `extent-2025-11-29-o70.geojson` | 158 KB | passes |
  | `extent-2025-11-29-o164.geojson` | 168 KB | passes |
  | `extent.geojson` (union of all passes, 42.05 km²) | 341 KB | **fails** the 300 KB budget |

- **Visual check (OpenStreetMap basemap):**
  - Water was detected north of the city, toward Khlong Hae, Khuan Lang and the Songkhla lake side, and in fields west and south.
  - **The city centre shows almost no water.** GISTDA reported 2–3 m there on 24 Nov, so this is the known Sentinel-1 urban double-bounce limit (median MERIT HAND in the city centre is 1.8 m, i.e. low-lying).
  - Northern flooding touches the AOI's north edge (7.15° N), so the AOI may need extending north.
- **Optical cross-check:** Sentinel-2 over the city centre was 100% cloud on 26 Nov and 28% on 1 Dec (after the peak). No usable optical image near the peak.
- **Bug fixed during the run:** `ImageCollection.max()` under-reported the union (39.31 vs 42.05 km²). The script now ORs the masks explicitly.
- **Comparison with EOS/AIT maps:** not done yet. It needs the reference file downloaded and its licence checked.
- **Decision:** superseded by run 2.

### hy-2025-11: run 2 (2026-10-12), current

- **Changes from run 1:**
  - The AOI is extended north to 7.25° N, so the flooding toward Songkhla lake is no longer cut off.
  - Defaults are now 30 m vectorising and 40 m simplification.
  - Coordinates are rounded to 4 dp (about 11 m), before the 0.5 ha filter is applied.
- **Detected area per pass:**

  | Bangkok time | Detected | File size |
  |---|---|---|
  | 24 Nov 06:03 | 35.50 km² | 289 KB |
  | 29 Nov 18:35 | 25.31 km² | 169 KB |
  | 30 Nov 06:01 | 21.63 km² | 178 KB |
  | Union (`extent-max-observed.geojson`, reference only, over budget, not shown in the app) | 46.23 km² | 390 KB |

  All three per-pass files pass the budget check.
- **App layers (`layers.json`, user decision 2026-10-12):**
  - Default: the 24 Nov 06:03 pass.
  - Toggle: the 30 Nov 06:01 pass ("water going down").
  - Also on by default: **reported flooding**.
- **Reported flooding (`reported-flooding.geojson`):** 17 public streets and landmarks with cited reports from 23–25 Nov.
  - Examples: Niphat Uthit 2/3 Rd "chest deep to over head height", Rat Uthit Rd "water to the ceiling", Kim Yong Market "waist to chest".
  - Locations are approximate, from OpenStreetMap. There are no household or personal details.
  - Places I couldn't geocode reliably were left out: Pom Hok community, Soi Sam Sakun 4, the PWA plant, and Wat Bang Sala (the OSM match was in another district).
- **Visual check:** the reported points fill the city-centre gap, where the satellite layer is blank.
- **Still to do:** compare with the EOS/AIT maps (needs the reference file and a licence check).

### hy-2025-11: "no satellite data" mask and planning geography v1 (2026-10-12)

- **Why:** Sentinel-1 can't see water between dense buildings (double-bounce). Like the Copernicus GFM exclusion mask, we ship those areas as "no satellite data", so nothing there is ever shown as dry (D26).
- **Method (`flood_check.py nodata`):** WorldCover built-up (class 50); share of built-up pixels within 200 m; kept where the share is over 50%; vectorised at 30 m; polygons under 0.3 km² dropped.
- **Result:** 20 polygons, 54.8 km², 75 KB. The Hat Yai core is one 28 km² polygon.
- **Check against the reports:** 16 of the 17 cited reported-flooding points fall inside the core polygon. Inside it, the 24 Nov pass detected only about 0.01 km² of water. The 17th point (Ban Phru, RPT-17) falls in a smaller built-up polygon to the south. This matches the expected blind spot.
- **Threshold choice:** 40% merged the core with surrounding villages (47 km²); 60% shrank it to 24 km² with the same 16 points. We use 50%.
- **Planning geography v1 (superseded for the city by v2 below):**
  - P-B (evacuation): B-1…B-5 in the city core, 2.0–3.3 km² each, 69–100% no satellite data. B-3 holds 7 of the reported points; B-4 has none (the "quiet zone" scene).
  - P-A (support in place): A-1 and A-2 north of the city, where the 24 Nov pass detected water among houses.
  - P-C (no recent assessment): C-1 and C-2 around Ban Phru (RPT-17: people on rooftops, 25 Nov).
  - 34 segments (one per landmark) and the shelter D1 on higher ground east of the core.
  - Rough size check (WorldPop 2020, 100 m): about 13,000–16,000 people in each city-core zone. The real per-segment estimate is Tuesday's task (D27).

### hy-2025-11: planning geography v2, city zones along streets (2026-10-12, D30)

- **District outlines:** the city's community map (PDF, a scanned image) was fitted to the OSM municipal boundary with an affine transform (median error 38 m), and the thick district lines were traced: เขต 1 4.7 km², เขต 2 6.1 km², เขต 3 4.5 km², เขต 4 4.0 km² (narrow edge strips are assigned to the nearest district).
- **Zones:** OSM trunk/primary/secondary roads, the railway, the river and canals cut the municipality into blocks; each block goes to the district holding most of it; blocks under 60 ha (or thinner than 40 m) merge with a neighbour in the same district. Result: 13 zones, 0.7–4.0 km².
- **Segments:** each zone is cut again along tertiary roads; pieces under 12 ha (or thinner than 25 m) merge. Result: 54 segments, one generic landmark each.
- **Scenes:** B-3 (เขต 2) holds 6 of the 17 reported points, the most of any zone, including Niphat Uthit 2/3; B-4 (เขต 2) holds none (quiet zone).
- **Rural zones** A-1, A-2, C-1, C-2 are unchanged from v1.


### hy-2025-11: people per segment (2026-10-12, D27, D31)

- **Command:** `flood_check.py exposure`, then `build_geography.py` (writes `exposure.json`; the ranges go into `segments.geojson`, `zones.geojson` and the C1 fixture). About 4 minutes.
- **Two counts per segment:** WorldPop 2020, and Open Buildings × 2.72 people per building (DOPA's 406,374 registered people / 149,430 buildings in the district). Each range spans both, rounded outwards to 2 significant figures. Across the district the two agree within 11% (WorldPop 449,262; buildings × rate 406,034); inside segments they differ more, so the ranges are wide on purpose (B-3: 7,900–13,000).
- **City model (D31):** water surface = mean FABDEM ground within 100 m of each report + the depth read from its words (low and high; 12 of 17 reports state a depth, table in `flood_check.py`), spread by inverse distance within 2.5 km; a pixel is likely flooded where the surface is more than 0.1 m above the ground. Shown only in city segments that are at least half "no satellite data". Reported ground heights 7–16 m.
- **City result:** the 24 Nov extent holds almost nobody in the city zones (0–60 people per zone), as D26 predicts. The model puts most of the core under water (B-3: 7,700–12,000 of 7,900–13,000 people); B-9 in the north-east comes out mostly dry (0–360 of 2,100–5,400).
- **Sanity check against GISTDA (25 Nov: 52,731 rai flooded, about 150,230 people affected in Hat Yai district):**

  | | Area | People |
  |---|---|---|
  | Satellite extent, 24 Nov, inside the district | 13,223 rai | 270–6,200 |
  | City model, "no satellite data" part only | 13,756 rai | 98,000–124,000 |
  | **Ours, total** | **26,979 rai (51% of GISTDA)** | **98,000–130,000 (65–87% of GISTDA)** |

  Same order of magnitude, and below GISTDA, as expected: one Sentinel-1 pass versus GISTDA's several passes plus RADARSAT-2 and HAND depth, and our model stops 2.5 km from the reports. The satellite alone finds about 4% of GISTDA's people, which is the case for D26/D31. For scale, relief was later paid to 185,650 households in the district ([Thansettakij, 17 Dec 2025](https://www.thansettakij.com/general-news/646798)), so "affected" in the relief sense is much wider than "living in flooded area".
- **Limits:** WorldPop 2020 spreads people into fields (A-1: 980 people in the extent by WorldPop, almost none by buildings). Buildings are not households. The model is a bathtub fill: no flow, drainage or timing. All of these are why the app shows ranges with the label "estimate", never a count.
- **Depth per segment (D32, same run):** each segment carries its FABDEM ground height (10th/50th/90th percentile) for live caller depths, and, where the city model is shown, the median modelled depth where flooded (low–high, 0.5 m steps). Uncapped, low ground north of the core (B-6, B-2) came out at 4–5.5 m, beyond any report, so the band is capped at the deepest report (3 m, "second floor"): 17 of 46 modelled segments read "over 3 m". The hot zone B-3 reads 1.5–3.5 m before the cap, in line with GISTDA's 2–3 m for the centre. Callers and teams replace the model as they report (D32).
