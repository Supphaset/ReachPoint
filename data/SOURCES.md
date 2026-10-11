# Flood data sources and runs

Every published layer must trace back to an entry here. See pack §5.1b–c for why each source is used.

## Inputs

| Source | Use | Licence / attribution |
|---|---|---|
| Copernicus Sentinel-1 GRD (`COPERNICUS/S1_GRD`, Earth Engine) | Flood change detection | "Contains modified Copernicus Sentinel data {year}" |
| JRC Global Surface Water 1.4 (`JRC/GSW1_4/GlobalSurfaceWater`) | Mask permanent water | Pekel et al. 2016, EC JRC / Google |
| SRTM 30 m (`USGS/SRTMGL1_003`) | Mask slopes over 5° | NASA / USGS |
| Sentinel Asia products (EOS, AIT), 23 Nov 2025 | Comparison only; not redistributed until the licence is checked | As stated on each product |

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
- **Decision:** pending. Choose the main layer and how to show the urban gap.
