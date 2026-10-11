# Map experience proposal

Date: 2026-10-11. Status: **Map emphasis requested by the human; interactions, layers, provider and final MVP remain proposed.** No application/map integration has been built. Companion to [product detail](product-detail.md), [PRD](prototype-prd.md), [wireframes](../design/wireframe-guide.md) and [accepted requirements](requirements.md).

## Purpose and placement

The map is a central working surface in Situation. It helps a coordinator relate flood evidence, exposed settlements, missing assessment and reviewed case locations before creating an owned next action. It is not a decorative overview or a count of victims.

| Surface | Proposed map behavior | Reason |
|---|---|---|
| Situation | Large map with layers, synchronized list and selected-area detail panel; map/list view switch. | Reveal potential exposure where no one has contacted the desk and make evidence inspectable. |
| Contact Center | Small location-review map in the case/event panel; current reported location, proposed location and any planned pickup have distinct labels. | Clarify landmarks and ambiguous location statements before accepting a case change. |
| Response | Map/list switch for tasks and authorized team/resource position reports; selected task opens its plan and constraints. | Understand spatial context while retaining ownership, dependencies and response feasibility checks. |
| Team mobile | Own-task location map, source/time and plain-text landmark/address alternative. | Communicate an assignment with minimum necessary details; avoid reliance on map tiles or continuous connectivity. |

No fourth coordinator navigation page is required. Same area/case/task ID links map, list and detail; selecting an object on either surface selects the same record, preserves filters and keeps the operator's place when returning.

## Layers and their meanings

| Layer | What may appear | Required distinction |
|---|---|---|
| Observed flood extent | Sourced observation polygon, acquisition time and quality. | Area footprint is not household water depth; absence of an observation is not absence of flooding. |
| Flood measurements | Individual station/field measurement markers with observation time, units and reference. | Gauge elevation and ground-relative depth are labeled separately; no continuous depth surface is inferred. |
| Forecasts/warnings | Separate forecast or warning geometry/markers, issue time and validity interval. | Forecast is never styled or titled as an observed condition. |
| Buildings | Footprint geometry/source date and overlap result under a frozen rule. | Detections are not households, occupancy, trapped people or residential use. |
| Population exposure | Separate modeled population layer or selected-area estimate with reference year/method/uncertainty. | Not a verified current headcount; cannot be summed with case counts. |
| Assessment coverage/gaps | Explicit reviewed observation scope/time; potential exposure lacking relevant current scoped assessment. | A completed attempt or one visited building does not clear the full area. |
| Cases and area reports | Authorized attributed location, uncertainty, case/report distinction and broad need status. | Unlocated records stay in a visible list. Shared phones do not collapse pins or establish identity. |
| Team/resource reports | Authorized own-team reported location/time, stale/unknown labels, availability kept separate. | Reported location is not continuous live GPS, capacity or suitability. |
| Tasks and facilities | Planned pickup/task scope; destination position only if supplied; acceptance/capacity source and time separately. | A facility marker does not mean it is open or accepting referrals; a task marker does not mean it has started. |

Default proposed Situation view: observed extent, buildings and assessment gaps; other layers opt-in to prevent clutter. The wireframe uses fictional roads and landmarks. Basemap/imagery provider, licensing, cost, accessible controls and source-backed data access remain unresolved. A future satellite basemap is distinct from dated flood-analysis overlays. No provider/framework selection is implied.

## Interaction details

- Pan and zoom; fit selected area/object; clear selection; visible layer controls and legend. Search scoped area/case/task/landmark references with permissions; ambiguous results require operator selection rather than automatic pin placement.
- Select an area to inspect building overlap, separate population estimate, assessment scope, source dates, missing data and a **Create assessment draft** action. Selection does not dispatch a team.
- Select a case to see a case reference, broad need status, location source/time/uncertainty and **Open case**. Exact medical details and contact numbers do not appear in map labels or general-purpose clusters.
- In Contact Center, a manually selected candidate landmark is a proposed location with provenance, not proof of presence. The operator must distinguish reported current location from planned pickup and approve the attributed event explicitly.
- Use separate shapes/text for observation, forecast, case, task and stale report. Clicking/focusing exposes details; important evidence never requires hover. Clusters count only the displayed record type, not people. Cluster details disclose provisional identity and exclusions.
- Source observation/acquisition time is always distinct from retrieval time. Compare only compatible source versions; no global 'live' indicator for mixed-age data. A historical flood layer does not time-travel current cases or tasks.
- Revised case location flags a pickup discrepancy; it never drags an assignment automatically. A coordinator explicitly reviews/revises the plan, then the team acknowledges its saved version.
- Proposed desktop structure: map occupies most of the main content, right detail panel, attention/unlocated list beneath or beside it. Narrow screens use list-first navigation and an optional own-task map with the same selected record.

## Failure and access states

Map tiles/loading failure leaves list, source text and owned tasks usable. A layer failure is labeled independently; cached or previous observations retain their original timestamp. Missing depth, unknown location and unavailable team positions are explicit unknowns. Approximate locations show their supplied boundary/accuracy basis; no invented numeric radius. If no accuracy is supplied, label it unknown.

Restricted roles cannot retrieve hidden record coordinates through search, clusters, exports or direct references. No public household map is proposed. Keyboard-operable list/detail provides every consequential action without manipulating the map. Visual map accessibility remains an implementation requirement, not a tested capability of these static drawings.

No route generation, route-safety score, automatic nearest-team dispatch, continuous GPS, imagery ingestion or custom satellite model is added to the lean scope. Spatial context supports evidence review; operational access and suitability require explicit checks.

## Proposed acceptance checks after implementation authorization

1. Selecting Area A in the map and list opens the same source/scope detail; a draft task retains the selected area boundary/version.
2. The synthetic 12/24 overlap remains building detections, while modeled population 120 remains a separate estimate and households/current occupancy remain unknown.
3. Missing local depth shows Unknown; gauge elevation never becomes ground-relative depth. Old imagery/extent retains acquisition time after a new fetch.
4. Unlocated H4 stays visible without a false pin; incomplete/provisional identity is not presented as a verified household total.
5. An approved H5 location change L1 to L3 leaves M1's old planned pickup intact until a reviewed revision. Map selection never starts a task.
6. A V1 availability report flags M1/M3 and preserves M2; no fabricated team position appears when its location is unspecified.
7. Tile/layer failure preserves useful list/detail work; denied coordinates and medical narratives remain inaccessible to unauthorized roles.
8. Keyboard/list flow performs selection, evidence inspection and draft creation without map-only controls.

These are proposed checks, not run tests. Expanded cartographic wireframes appear on PDF pages 10–11; the Contact Center inset and team own-task map are specified here but not additional drawn screens. First implementation slice, if later authorized: one bounded map, one source fixture, area selection and synchronized list/detail. Verify provider/data/phone feasibility separately before broadening scope.
