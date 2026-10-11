# Updating the flood situation

Date/access date: 2026-10-11 (Asia/Bangkok). Status: research and proposed approach; no feed integration, accounts, calls, scraping service or deployment. Thailand is the research assumption; no local operating geography is selected.

## Available source categories

| Source | Information it can contribute | Access evidence and limitations |
|---|---|---|
| F1 ThaiWater / HII | Rainfall, station water conditions and forecasts/context. | Official mobile-page description and HII standards inspected. Standards document rainfall/runoff/station metadata; they do not establish a permission-free live endpoint. Main dashboard yielded no readable text; no live readings or station cadence verified. |
| F2 TMD radar | Rain observations and storm context. | Public radar page accessible. Rain is not observed inundation or household water depth. No station coverage/cadence/API license test. |
| F3 GISTDA Disaster Platform | Satellite-derived observed flood extent and impact context. | Official indexed article describes near-real-time products and map/table/PDF/GIS outputs. Direct article fetch failed; services page yielded no text. Catalog/download paths surfaced, but no actual local layer or update interval verified. |
| F4 Google Flood Hub/API | Forecasted riverine flooding status; API schema includes forecasts and inundation maps. | API documentation accessible, Thailand listed in official coverage page. API requires waitlist approval, a key and enablement; none obtained. Local coverage, lead time, terms and access timing need checking. Not a universal flash-flood or street-depth source. |
| F5 DDPM | Administrative disaster situation and impact reports. | Official disaster-report system indexed as seven-day reporting; direct fetch returned 502. Affected-area summaries do not establish exact present inundation. |
| Reviewed local reports | Specific observations, access failures and ground-relative depth where actually measured/reported. | Proposed operator/team/resident input, not a confirmed partner/feed. Retain attribution, location, observation time, method/reference, units and uncertainty; contradictions remain visible. |

Sources/limitations are in [sources](sources.md). These are ways to obtain evidence, not a verified report of today's flood conditions at any location. Search crawl time and webpage retrieval time do not establish observation freshness. Dashboard zero/blank output may reflect missing data; never interpret it as no flooding.

## Recommendation for the prototype

Propose a Flood situation layer within Operations, with four separate categories: **observed extent**, **station observations**, **forecast/warning**, and **reviewed local reports**. Reuse the existing map/context drawer; no new main page.

Every item retains publisher/source ID, geographic footprint or station, observation/acquisition time, publication time, retrieval time, units/reference where relevant, product/version, validity interval and uncertainty/quality. Set freshness rules by data type and operator review; polling more often does not make a satellite image newer. Show unavailable, stale and conflicting inputs plainly.

Potential update workflow: a new source item is validated and compared with an earlier compatible version; changed exposure can propose an assessment-gap review. Human reviewers choose outreach/reassessment. A new flood layer never automatically proves a building is occupied, creates household cases, closes a need, supplies a safe route or dispatches a team. Rainfall changes and gauge changes remain their own measurements; neither is converted directly into household depth.

Start after authorization with one bounded locality, one verified observational source and timestamped local reports. Add forecasting only if access and coverage are demonstrated. Human-reviewed timestamped imports are a candidate fallback when lawful automated access is unavailable; disclose import freshness and manual provenance. Until actual feed access is verified, use labeled synthetic observations for the workflow rather than implying a live map.

## Feasibility gate and proposed tests

Before selecting any feed, verify local coverage, source authorization/license, accessible format, observation/publication cadence, units/datum, attribution, quality flags, rate limits/costs and stale/missing recovery. No undocumented endpoint copied from third-party code is an established public API contract. Google waitlist timing must not block the core workflow.

Proposed tests: old item retrieved today stays old; station elevation is not ground-relative depth; forecast is not observation; absent tile is unknown, not dry; compatible extent updates use frozen boundary/overlap rules; conflicting field reports preserve attribution; replay does not duplicate exposure/actions. The satellite building baseline and flood acquisition may be years apart; retain this mismatch. Do not claim live reliability until actual data access and update behavior have been tested.
