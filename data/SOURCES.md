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
