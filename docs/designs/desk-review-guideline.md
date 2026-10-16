# Caller desk evaluation guideline

Updated 16 Oct 2026. Synthetic demo recommendations require human approval. This policy does not establish clinical assessment, vehicle wading capability, safe routes or dispatch. See [0017](../decisions/0017-desk-depth-threshold-and-evaluation.md).

## Transport planning

Gemini extracts current numeric water measurements with exact caller quotes and scope. The server verifies the number/unit conversion and applies the user-selected **50 cm** boat preference.

| Reported facts | Recommendation |
|---|---|
| Exact depth **50 cm or higher** | Boat candidate; confirm actual access |
| Exact **access-road/path** depth below 50 cm | Truck candidate; confirm route/vehicle suitability |
| Explicit dry road access | Truck candidate |
| Access road/path cut off by water or deep access flooding | Boat candidate; confirm suitability |
| Reported waist/chest/head-level water around people | Provisional boat preference; exact depth/access remain unverified |
| Strong current, structural/electrical hazard or conflicting reports | Needs specialist assessment |
| No measured depth or usable access description | Needs assessment; collect depth/access details |

An indoor measurement at or above the threshold can suggest a boat for initial planning. An indoor measurement below it does not establish road access. **“First floor flooded / ท่วมชั้นหนึ่ง” does not establish 50 cm of water**: it identifies the affected floor. Never convert floor labels or assumed building heights into water depth. Ranges, uncertain quantities and historical/hypothetical measurements remain unresolved as exact current measurements.

The 50 cm preference is a user-selected demo rule, not an official safe-driving cutoff. [NWS flood guidance](https://www.weather.gov/safety/flood-during), accessed 16 Oct 2026, warns against entering flooded roads and describes moving-water and hidden-road hazards. A depth threshold alone cannot clear a route or determine boat/truck suitability.

## Emergency recommendation

Evaluate current reported evidence in the following order. Require supporting caller quotes; retain context and negation. These labels are ReachPoint's demo categories.

| Level | Rule | Examples |
|---|---|---|
| **1a — suspected medical emergency** | Serious current medical warning signs requiring qualified assessment | Unresponsive, severe breathing difficulty/not breathing, heavy uncontrolled bleeding, ongoing convulsions |
| **1b — urgent rescue** | Immediate threat to people from flooding or related hazards | Being swept away; trapped in rising water with no safe refuge; imminent structural/electrical danger |
| **2 — assistance needed** | Active food, drinking water, regular medication or evacuation request, pending any more urgent reported sign | Selected food/evacuation request; children hungry and needing water; assisted evacuation |
| **3 — routine/non-emergency** | Explicit safe circumstances and routine/non-urgent need | Safe household requesting a non-urgent supply delivery for later |
| **Unresolved** | No usable request/danger evidence or model failure | Historical row with no help type or usable narrative; failed model reading |

Medical warning-sign examples are informed by the indexed excerpt of the [NIEMS public emergency guide](https://www.niems.go.th/1/upload/migrate/file/255912201429421769_DnRyGchSR1ODAHUz.pdf), checked 16 Oct 2026; fetching the full PDF timed out. That source does not validate this AI workflow or define these numerical labels. Medical assessment requires qualified personnel. Age, disability, deep water or a medication mention alone does not establish a medical emergency.

Current hunger/thirst is Level 2 evidence even without the word “urgent.” A caller-confirmed food/evacuation type establishes a request for assistance; after a successful model reading it defaults to Level 2 unless stronger signs or explicit routine/non-urgent evidence apply. This does not confirm absence of danger or clinical assessment. Missing information never defaults to Level 3. The reported-danger safety floor overrides routine model interpretations. Original statements, AI recommendations, human corrections and approval/history remain separate.
