# Judge Q&A

Current v2 answers, 17 Oct 2026. [English demo](https://reachpoint-main.web.app/?lang=en),
[implementation overview](../../README.md#how-it-works), [Google Cloud stack](../../README.md#google-cloud).
All people, conversations and plans in this demo are synthetic.

1. **What does Gemini do that a static form cannot?**
   The intake agent follows a conversation, asks for missing facts, locates the household and can clarify a
   neighbour's compass direction on a building picture. The hybrid reader uses Gemini Flash-Lite first, checks
   extracted quotes against the message, and fills gaps with rules. The copilot uses Flash function calling to
   inspect zones and draft a trip from current evidence. Show the labelled reader and actual tool calls;
   a rules fallback is not a live Gemini result. [Intake](../../api/v2/intake.py), [reader](../../api/v2/ai.py),
   [copilot](../../api/v2/copilot.py).

2. **How does voice work?**
   Gemini Live carries audio through the browser's call screen and the Cloud Run WebSocket into the same v2 intake
   workflow as typed chat. There is no real telephone line. Thai/English voice exists, but audio accuracy in noise
   and different accents has not been measured. [Voice](../../api/v2/live.py), [client](../../web/src/features/v2/liveVoice.ts).

3. **Why trust the extracted facts or the household count?**
   A quote proves provenance, not truth. The locator uses Pinpoint when available and a labelled street-name match
   otherwise. Dedupe keeps conversation history and uses conservative household matching; possible matches remain
   a range. Shared phones do not identify a household. On the synthetic evaluation, 306–309 households versus 299
   means the lower bound is within 3%, while the upper bound is 3.3% high; wrong merges were 1%.
   [Pipeline](../../api/v2/pipeline.py), [evaluation](../eval/v2-results.md), [current figures](../../README.md#measured-not-claimed).

4. **Does the flood map know the real water depth?**
   No. A local-inertial basin model on 75 m terrain provides the prior; dated reports correct it locally with
   uncertainty. OSM streets, terrain, IMERG rain, satellite inputs and the gauge have separate roles. Satellite
   extent is not depth. Contradictory reports are labelled doubtful and retained; missing reports do not mean dry.
   The leave-one-out synthetic household depth error was 0.27 m versus 0.46 m for the model alone, not field validation.
   [Model](../../data/scripts/build_v2_basin_sim.py), [assimilation](../../api/v2/assim.py).

5. **What happens after someone reports?**
   Planner/notifier logic schedules check-ins, warns about rain and rising water, flags lost contact and sends zone
   plan updates to families. Shelter cards show candidate public buildings and an OSM street walk check, with a
   labelled direct-line fallback. They do not certify safe routes or official shelter availability. English sessions
   receive English messages and place names. [Planner](../../api/v2/planner.py), [follow-up](../../api/v2/followup.py),
   [shelters](../../api/v2/shelters.py).

6. **Who decides where a team goes?**
   Volunteers inspect Water, Urgent and Do first, open a zone, choose I'll go here and post a reviewed plan.
   The copilot proposes evidence-linked runs and kit; deterministic checks validate its numbers. It cannot promise
   arrival or assign teams. The mission page offers directions and outcome recording. Picked up is a team report;
   the family is asked to confirm, so a plan, delivery report and confirmed receipt remain distinct.
   [Volunteer views](../../api/v2/cases.py), [mission](../../web/src/features/v2/volunteer/MissionPage.tsx).

7. **What happens on restart or if Gemini fails?**
   Active rooms are in memory; when RP_FIRESTORE=1, store.py debounces persistence of room state to Firestore and
   restores it on demand after restart. A recent unflushed update or failed save can still be lost. The reader and
   copilot have labelled rules fallbacks; voice can become unavailable. The deploy script uses one always-on
   Cloud Run instance with session affinity, not a demonstrated multi-instance coordination system.
   [Storage](../../api/v2/store.py), [deployment](../../scripts/deploy.sh).

8. **Where are Google Cloud and Firebase used?**
   Gemini Flash-Lite reads, Flash calls copilot tools and Gemini Live handles voice. The default deploy route is
   the Gemini API key; Vertex is optional. Cloud Run serves one web/API container, Firestore persists rooms,
   Firebase Hosting fronts Cloud Run, and voice connects directly to Cloud Run. Earth Engine precomputes inputs,
   Maps supplies map context, and Secret Manager injects credentials. The repository config establishes intended
   settings; this review did not inspect private cloud settings. [Stack](../../README.md#google-cloud).

9. **How do you protect exact locations?**
   Volunteer case views unlock synthetic addresses for a named team with a plan covering that zone. Source
   messages remain evidence. Room isolation and these view filters are demo boundaries, not production identity
   verification: stronger authentication and authorization still need work. Only synthetic personal data is allowed.
   [Case views](../../api/v2/cases.py), [data handling](../collaboration/data-handling.md).

10. **What impact, differentiation and cost have you proved?**
    The demonstrated loop joins intake, household matching, flood estimates, coverage gaps, plans and family updates.
    The evaluation is a team-authored synthetic scenario: 1,517/1,522 = 99.7% Gemini-labelled readings with rules
    filling gaps, 4/5 planted wrong reports caught, and 72/72 neighbour buildings matched. This does not establish
    adoption, rescue outcomes or superiority to other tools. A responder drill and measured operating costs are next;
    no operator or payer is confirmed. [Limits](../../README.md#honest-limits), [evaluation](../eval/v2-results.md),
    [research](../research/real-rescue-practice.md).
