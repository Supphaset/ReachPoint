# ReachPoint

**A flood picture that builds itself from what people say.** Families talk to an AI agent; the demo replays synthetic public posts and reconstructed
bulletins alongside historical river-gauge and satellite inputs. A team of agents turns all of it into one live
map for volunteers: who needs help, how deep the water is street by street, where it is heading, and who plans to
come. Then it tells every household what is happening.

AI Builder Cup 2026 (Google Cloud JAPAC) · Sustainability & Social Impact · built during the event (planning from 11 Oct, code 12–18 Oct 2026) by a team of two.

- **Live demo:** [Open in English](https://reachpoint-main.web.app/?lang=en) (Firebase Hosting; the same app on Cloud Run directly: [run.app](https://reachpoint-900867850704.asia-southeast1.run.app/?lang=en))
- **Repository:** [Supphaset/ReachPoint](https://github.com/Supphaset/ReachPoint) · **Video:** see the submission · **Deck (PDF):** see the submission
- Product spec: [`docs/product/v2-spec.md`](docs/product/v2-spec.md) · Evaluation: [`docs/eval/v2-results.md`](docs/eval/v2-results.md)

## The problem

In the November 2025 Hat Yai flood, help requests arrived faster than anyone could sort them:

- A Hat Yai rescue volunteer group told Reuters calls had come in non-stop, in the thousands, for three days
  ([Reuters, 25 Nov 2025](https://www.marketscreener.com/news/thailand-to-send-aircraft-carrier-for-flood-relief-as-rains-intensify-ce7d5edddb80f122)).
- The government's crisis centre merged requests from Traffy Fondue, the HatYaiFlood site and volunteer groups into
  about 40,000 cases covering 77,000 people, and said the data was still incomplete because names didn't match across
  entries ([The Nation, 27 Nov 2025](https://www.nationthailand.com/news/general/40058844)).
- Being heard was not the same as being reached. A mother who spent two days on her roof with her four-year-old said:
  *"Every day they would pick up my calls, but nobody came to rescue us."*
  ([ABC News, 30 Nov 2025](https://www.abc.net.au/news/2025-11-30/thailand-floods-death-toll-rises/106082418))
- Phone lines and power failed, so many people lost contact
  ([Thai PBS, 25 Nov 2025](https://www.thaipbs.or.th/news/content/358821)); false or incomplete messages cost rescue
  teams time ([Bernama, 27 Nov 2025](https://www.bernama.com/en/news.php?id=2496089)); and a later white paper found no
  system tracked which areas had been reached and which were still waiting
  ([ThaiPublica, 21 May 2026](https://thaipublica.org/2026/05/hatyai-flood-systemic-failure-analysis/)).

So nobody could say how many people were in which street, how deep the water was there, or whether anyone was on the
way. More sources: [`docs/research/real-rescue-practice.md`](docs/research/real-rescue-practice.md).

### What existed, and what ReachPoint adds

Volunteers built real tools during the flood: Traffy Fondue and the HatYaiFlood site collected requests, Jitasa.Care
used AI to sort about 20,000 social-media posts by need and location, and ThaiRod on LINE showed rescuers the nearest
open cases ([Thairath](https://en.thairath.co.th/news/politic/2897779),
[Spring News](https://www.springnews.co.th/news/hot-issue/860848)). ReachPoint demonstrates a connected picture of requests, water estimates and team plans:

- **One family, one dot.** Messages, forwards and relatives' posts are matched to households, with
  merge reasons and possible-duplicate ranges shown, so 1,064 messages become about 300 families.
- **People's words correct a physics flood model.** "Water at my waist" becomes a reported depth range that updates the
  water street by street, and the model tells volunteers where to expect water nobody has reported.
- **The silent are counted.** Zones the model says are flooded but nobody has reported from are flagged, and the
  agent asks people there about their neighbours.
- **Volunteers see what is still missing.** Zones with families and no team, a copilot that plans a trip from the
  evidence, and every posted plan told to the families it covers.

## Try it in 90 seconds

Open the site. You get your own private demo room (nobody else sees your reports; Reset only resets yours). The step
bar at the top walks you through it; **Explore freely** opens everything else.

1. **Overview.** The flood week replays in 20 seconds: water spreading from the hills and canals, messages arriving,
   duplicates merging, and the counter settling at 1,064 messages → about 300 families. The right column shows what the
   AI is doing, each line marked by who decided: **Gemini** (reading), **rules** (matching, merging), **physics**
   (the flood model) or **action**.
2. **Report as a family.** English mode prefills English. Send:
   *"Water is up to my waist, I'm with my mom who can't walk, house 52/9 Phetkasem Soi 2"*.
   Or press **Call** for browser voice through **Gemini Live**. Inspect the location, quoted facts, trace,
   water estimate and shelter card; choose **Need a team** and tick the get-ready checklist.
   Optional Thai example: *"น้ำถึงเอวแล้ว อยู่กับแม่ แม่เดินไม่ได้ บ้านเลขที่ 52/9 ถนนเพชรเกษม ซอย 2"*
   means *"Water is up to my waist; I'm with my mother, who cannot walk; house 52/9, Phetkasem Soi 2."*
3. **Volunteer.** Turn on **Water**, open **Urgent**, set a synthetic team name and mark **Do first**.
   Open zone **D12**, choose **I'll go here**, check the plan and post it. The **Mission** page shows
   directions and **Picked up**. A team report prompts the family to confirm; it does not prove receipt.
   The copilot also accepts *"I have one boat with 6 seats. Where first?"* and shows Gemini's tool calls.
4. Return to the family phone to see its plan update. D12 is a separate example zone: the sample address
   resolves to **B5**, so post a B5 plan too to demonstrate an update to this same family.
5. **Demo controls** are bottom-right behind **Demo ⋯**: +30 min, Rain alert, River rising,
   Flood the system and Reset. Reset affects only your demo room.

## How it works

```mermaid
flowchart LR
  V["Victims: chat or voice"] --> I["Intake agent"]
  P["Public posts"] --> RD["Reader"]
  B["Bulletins, gauge X.44"] --> RD
  S["Sentinel-1, IMERG rain, FABDEM terrain"] --> SIM["Flood simulation"]
  I --> L["Locator: address → building,<br/>'house to the east' → building"]
  RD --> L
  L --> D["Dedupe: households, not reports"]
  D --> A["Analyst: words → depth,<br/>simulation corrected by reports,<br/>doubtful reports"]
  SIM --> A
  A --> PL["Planner: whom to ask,<br/>whom to warn first, lost contact"]
  PL --> N["Notifier: Thai or English session messages"]
  VP["Volunteer: one-line plan"] --> PL
  A --> BD["Board: zones, depth map,<br/>time-lapse, AI activity"]
```

| Step | What it does | Code |
|---|---|---|
| **Intake agent** | One question at a time, only what is missing: where, how many, who is vulnerable, how deep (with a concrete check: "above or below your door handle?"). Neighbours only when the person mentions them: their direction if missing, then a yes/no on the satellite picture. Offers a walkable shelter. Typed, held mic, or a Gemini Live call | [`intake.py`](api/v2/intake.py), [`live.py`](api/v2/live.py) |
| **Reader** | A language model turns any message into facts. Every fact must quote the person's exact words or it is dropped. The hybrid reader uses Gemini first; rules fill missing facts and handle unavailable models, with the reader labelled | [`ai.py`](api/v2/ai.py), [`reader.py`](api/v2/reader.py) |
| **Locator** | Address → Pinpoint → the Google Open Buildings outline under it. "The house to the east" → the nearest building in that compass sector (compass, because left and right depend on where you face) | [`geo.py`](api/v2/geo.py) |
| **Dedupe** | Counts households, not messages. Replies stay in their conversation; a relative's post merges only when exactly one nearby family has the same makeup; otherwise it is kept apart and counted as a range | [`pipeline.py`](api/v2/pipeline.py) |
| **Flood model** | Local-inertial shallow water (Bates et al. 2010) over the whole lower U-Tapao basin: IMERG rain, curve-number losses, Manning friction by land cover, canals, city drains that back up, Sadao inflow, Songkhla Lake. 75 m basin terrain; street-level ground in dense blocks. Calibrated against the real gauge and news-reported depths | [`build_v2_basin_sim.py`](data/scripts/build_v2_basin_sim.py) |
| **Analyst** | Words → depth ranges with an error by wording and source. Optimal interpolation spreads each report's gap from the model (≈300 m, 12 h); where the model is dry but people report water, the water fills only the low ground. A report the model and its neighbours both contradict is marked doubtful, never deleted | [`assim.py`](api/v2/assim.py) |
| **Planner, Notifier** | Daily and alert check-ins; rain warnings with each home's expected rise from an extra-rain model run; "lost contact" after two missed checks; plan updates to every household in a zone; gaps such as "nobody plans medical help" | [`planner.py`](api/v2/planner.py), [`rain.py`](api/v2/rain.py) |
| **Shelters** | Real public buildings (OSM) that stay dry all week in the model and have no deep-water report nearby; a walk check along the way; check-in by the family, a team or shelter staff | [`shelters.py`](api/v2/shelters.py) |
| **Volunteer pages** | Where help is missing, live feed, zone, family case, plan a trip; exact addresses only for a team whose plan covers the zone | [`cases.py`](api/v2/cases.py), [`web/src/features/v2/volunteer`](web/src/features/v2/volunteer) |

**Which model:** Gemini reads every message (`REACHPOINT_LLM=gemini`, the default) and Gemini Live (`gemini-3.8-live`)
is the voice. During development the same reader also ran on Claude through the Claude Code CLI, to compare; every
reading is labelled with the model that made it.

## Google Cloud

- **Gemini:** Flash-Lite reads messages with quoted evidence; rules fill gaps. Flash powers the copilot
  with [function calling](https://ai.google.dev/gemini-api/docs/function-calling/), and **Gemini Live**
  handles browser voice. The deploy script defaults to the Gemini API key route; Vertex AI is optional.
  Actual model identifiers are shown in reader/tool traces rather than treated as accuracy guarantees.
- **Cloud Run:** one container serves React and FastAPI. The demo deploy configuration sets minimum and maximum
  instances to one, keeps CPU allocated (always-on), and enables session affinity for voice reconnections.
  See [deploy.sh](scripts/deploy.sh) and [minimum-instance documentation](https://docs.cloud.google.com/run/docs/configuring/min-instances).
- **Firestore:** [store.py](api/v2/store.py) persists synthetic demo-room clocks, sessions, reports, plans and
  Do-first marks when `RP_FIRESTORE=1`; debounced writes restore rooms after restart. In-memory state still
  serves active rooms; this is not a multi-instance transaction design.
- **Firebase Hosting:** configured as the CDN entry point in front of Cloud Run via
  [Hosting rewrites](https://firebase.google.com/docs/hosting/cloud-run) ([firebase.json](firebase.json)).
  The voice WebSocket connects directly to Cloud Run. The demo link above goes through Firebase Hosting; the run.app address reaches Cloud Run directly.
- **Earth Engine:** offline preparation of satellite, rainfall, terrain and land-cover inputs; no live Earth
  Engine requests during the demonstration. **Google Maps** provides satellite context and directions links.
- **Secret Manager:** holds server-side API credentials injected into Cloud Run; keys stay out of source and
  browser responses. See [Secret Manager documentation](https://docs.cloud.google.com/secret-manager/docs/overview).

Configuration evidence is in the linked code; it does not by itself verify deployed service settings.
Public documentation checked 17 Oct 2026; [source register](docs/research/sources.md).

## Measured, not claimed

[`docs/eval/v2-results.md`](docs/eval/v2-results.md), reproduced with `python api/scripts/eval_v2.py`, on the Hat Yai
scenario (real water data, synthetic people and messages, with deliberately wrong reports planted):

| Measure | Result | Target |
|---|---|---|
| Hybrid reader: Gemini first, rules fill gaps; labelled by reader | 1,517 of 1,522 = 99.7% Gemini-labelled (5 rules-only) | — |
| Depth at a household from the model + other reports (that report left out) | 0.27 m mean error; the model alone 0.46 m | better than the model alone |
| Families counted against the synthetic reference families heard about | 306–309 vs 299: lower bound within 3%; upper bound 3.3% high | lower bound within 3% |
| Two families wrongly merged into one | 1% | ≤ 3% |
| Planted wrong reports flagged doubtful | 4 of 5 | ≥ 80% |
| Honest reports wrongly flagged | 5% | low |
| "The house to the east" matched to the exact building | 72 of 72 | ≥ 85% |

The scenario's "true" flood is the simulation plus local effects it can't know (blocked drains, pumps, smooth
differences), so these numbers show how well physics and reports combine, not field accuracy.

## Data

| Real | Synthetic |
|---|---|
| River gauge X.44 (RID), IMERG rain, Sentinel-1 flood extent, FABDEM terrain, ESA WorldCover (Earth Engine), Google Open Buildings outlines (30,086 in the city), OSM streets ([English name inventory](docs/research/hat-yai-place-names.md)), canals and public buildings, news-reported depths (23–25 Nov), WorldPop and DOPA population | Every household, message, post, reply and volunteer plan. Bulletins are reconstructed from the real gauge readings and labelled as such |

Never enter real personal data.

## Honest limits

- **The flood model is a model.** Against the real data it runs about 1.2 m high at the gauge on average and drains too
  slowly, and downtown on 23 Nov it gives 0.3–0.7 m where people reported 0.5–2 m. Reports correct it where people
  talk; elsewhere it is labelled as the model.
- **Synthetic people.** The scenario was written by the team; the evaluation measures behaviour, not field accuracy.
- **Shelters are candidates,** not the official 2025 list; room is estimated from building size. The walk check follows OSM streets where a route exists, with a labelled direct-line fallback; neither establishes a safe route.
- **Rain warnings are linear:** one extra-rain run scaled to the forecast.
- **Not tried with responders yet.** No drill with a rescue team so far.
- **Messages are simulated.** Check-ins appear in the app; SMS, LINE and real phone calls are not connected. Gemini
  Live works in the browser.
- **Pinpoint:** where the key is not configured, addresses fall back to a street-name match in the city.

## Run it locally

```bash
python -m venv .venv && .venv/bin/pip install -r api/requirements-dev.txt
(cd web && npm ci && VITE_DATA=api npm run build)
.venv/bin/python -m uvicorn api.main:app --port 8093     # http://localhost:8093
.venv/bin/python -m pytest -q api/tests && (cd web && npm test)
```

Rebuild the data: `data/scripts/build_v2_buildings.py`, `fetch_v2_streets.py`, `build_v2_terrain.py` (Earth Engine),
then `build_v2_flood_sim.py`, `build_v2_scenario.py`, `api/scripts/v2_batch_read.py`, `python -m api.v2.board`
(time-lapse summary) and `api/scripts/eval_v2.py`. The earlier role screens (coordinator desk, team screens) are
still in the code at `/classic`.
