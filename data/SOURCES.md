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

### hy-2025-11: not run yet

- Date run:
- Project:
- Scenes used (date · platform · pass · orbit):
- Parameters: diff_db -3, water_db -15, smooth 30 m, slope < 5°, permanent water ≥ 80% masked, min 8 px, scale 20 m
- Flooded area (max extent):
- Comparison (reference · IoU · share of reference detected):
- Notes (urban under-detection, missing dates, anything odd):
- Decision: use our extent / use the published fallback
