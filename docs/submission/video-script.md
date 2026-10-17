# Demo video — aim for 3:30

Record at [the deployed English URL](https://reachpoint-900867850704.asia-southeast1.run.app/?lang=en).
Allowed length: 3–4 minutes; target 3:30, acceptable edit 3:00–3:45. Video and deck links: see the submission.
Keep the synthetic-data disclosure visible. Demo controls are bottom-right behind **Demo ⋯**.

## Recording setup

Use one fresh demo room throughout, with the family phone and volunteer page in the same browser profile.
Keep the family tab open so its session survives the mission scene. Do not reset between scenes.
Use the English sample, editing its street before sending to keep this story in **D12**:

> Water is up to my waist, I'm with my mom who can't walk, house 52/9 Lamai Songkhro

The unedited prefill says Phetkasem Soi 2 and resolves to **B5**, not D12. Do not imply a D12 plan covers B5.
Set the synthetic team name to **Demo Boat 1**, boat, 6 seats. Arrival time is the team's plan, not an AI promise.

## Shots and voice-over

| Time | Current clicks / what to show | Voice-over |
|---|---|---|
| 0:00–0:25 | **Overview** → play the flood week. Pause at **25 Nov 06:00**. Show 1,064 messages and 307 households, then the agent activity. | “During a flood, a message can be heard without a family being reached. ReachPoint joins reports, water conditions and volunteer plans. This is Hat Yai's historical flood, with synthetic people. Play the week: more than a thousand messages become about three hundred households, with the evidence still attached.” |
| 0:25–0:55 | **Report as a family** → edit the sample street to **Lamai Songkhro** → send. Show the **location** card and map. If the agent asks the household size, answer **2 of us**. | “A family can type or use Gemini Live browser voice. Here, water is at waist height and the mother cannot walk. The Gemini reader extracts quoted facts, with rules filling gaps. The locator matches the reported street to a building in D12. This street-name fallback is labelled; it is not a verified household address.” |
| 0:55–1:20 | Open the report **trace**. Show the reader label, D12 location and water correction. Show the **shelter card**: **Wat Klong Rian**, **1.3 km**, **27 minutes**, deepest **1.43 m**, street route. | “The trace shows what was read and how the location was chosen. At this house, the model gives 1.28 metres; reports correct it to about 1.07, with a range. The nearest candidate shelter is Wat Klong Rian. The street walk check reaches 1.43 metres, so the agent says not to wade. This is planning evidence, not a safe-route guarantee.” |
| 1:20–1:40 | Select **Need a team** on the shelter card. Show the recorded request and tick the **get-ready** checklist. Keep the family phone open. | “The family needs a team. The request stays open while they prepare. A request for help does not mean a team has accepted, and a plan will not be presented as a completed rescue.” |
| 1:40–2:15 | **Volunteer** → map → **Water** → **Urgent** tab. Set **Demo Boat 1**, select **Do first** for a visible urgent case. Open zone **D12**. | “Volunteers see the water estimate alongside families still waiting. Urgent keeps reported danger visible; Do first records a team's priority mark. Before this new report, D12 had seven families waiting, eighteen people and three urgent cases. The new report changes the live counts. Each number comes from the current records.” |
| 2:15–2:40 | D12 → **I'll go here** → review boat, seats, arrival time and plan → **post plan**. Open **Mission**. | “Our team chooses D12 and posts its own plan. The notifier sends that update to families in the zone. The Gemini copilot can also call tools to inspect needs and draft runs, but people review the plan and decide where to go.” |
| 2:40–3:00 | **Mission page** → show **directions** → select a synthetic household → **Picked up** → confirm. Return to the family tab. | “The mission page turns the plan into a visiting list with directions. Picked up records a team report, then asks the family to confirm. Directions are a map link, not a claim that the route is safe.” |
| 3:00–3:15 | Family phone: show the **plan update** from Demo Boat 1. If recording the pickup for this same family, also show its confirmation question; retain the earlier plan update in the inbox. | “Back on the family phone, the plan update says who plans to come. The family can answer and correct the record. Planned help, a team report and confirmed receipt stay separate.” |
| 3:15–3:30 | Close on the **Google Cloud stack slide**, live English URL and [repository](https://github.com/Supphaset/ReachPoint). | “Gemini reads and calls planning tools; Gemini Live carries voice. Cloud Run hosts the web and API, Firestore persists demo rooms, and Firebase Hosting fronts the service. Earth Engine prepares flood inputs; Google Maps adds context. ReachPoint connects what people say to what teams plan—and what families can actually confirm.” |

## Live API evidence for the capture

Checked by `curl` on **17 Oct 2026**, direct Cloud Run URL above, isolated synthetic rooms.
These are observed outputs, not exact values to force if a later build or a new report changes them.

- `GET /api/v2/v/overview`: **1,064 messages**, **307 households**, **1,102 people**, at **25 Nov 06:00**.
- `GET /api/v2/v/zones/D12`: **7 open families**, **18 people**, **3 urgent**, **6 needing a boat** before the new report.
- English session + the Lamai Songkhro sample: reader **gemini:gemini-flash-lite-latest**;
  location **D12**, by **street name in the address**; household **HH308** in that fresh room.
- Sample trace: model **1.28 m** → corrected **1.07 m**, likely **0.73–1.41 m**.
- Shelter route: **Wat Klong Rian**, **1.3 km**, **27 minutes**, deepest **1.43 m**, `by: streets`, `walkable: false`.
  The agent says: “The nearest shelter is Wat Klong Rian, about 1.3 km away”, followed by the deep-water warning.
- The unedited Phetkasem sample was also checked: **B5**, **Prince of Songkla University**, **2.6 km**,
  **52 minutes**, deepest **1.08 m**. These outputs belong to a different location; do not mix the two shots.
- Plan, pickup and family-inbox wording should be captured from the actual recorded interaction; those live writes
  were not performed for this documentation check. The walkthrough follows the current local UI handlers.

## Final recording checks

- [ ] Deploy the English place-name changes before recording; this task does not deploy them.
- [ ] Confirm `?lang=en`, English prefill, English place labels, and the actual Gemini/rules labels.
- [ ] Use the D12 sample edit above; verify D12 in the returned location before posting the plan.
- [ ] Check Maps, the water layer, the shelter card and the report trace on the deployed revision.
- [ ] Browser voice is optional in this timed sequence; do not claim a real phone call or tested audio accuracy.
- [ ] Show only synthetic reports; keep credentials, room/session tokens and account panels out of the recording.
- [ ] Use actual counts on screen after the new report; retain the explicit “before the report” qualification.
- [ ] Check the final exported duration: target **3:30**, within **3:00–3:45** and the allowed **3–4 minutes**.
