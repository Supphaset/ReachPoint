# ReachPoint

**A flood picture that builds itself from what people say.** Victims talk to an AI agent; public posts, official
bulletins, the river gauge and satellite passes come in on their own. A team of agents turns all of it into one live
map for volunteers: who needs help, how deep the water is street by street, where it is heading, and who plans to
come. Then it tells every household what is happening.

AI Builder Cup 2026 (Google Cloud JAPAC) · Sustainability & Social Impact · built 12–18 Oct 2026 by a team of two.

- **Live demo:** _link added at deploy_ · **Video (under 3 min):** _link added on submission_ · **Deck (PDF):** _link added on submission_
- Product spec: [`docs/product/v2-spec.md`](docs/product/v2-spec.md) · Evaluation: [`docs/eval/v2-results.md`](docs/eval/v2-results.md)

## The problem

In the November 2025 Hat Yai flood, tens of thousands of requests for help came in through phone lines, Facebook
groups, LINE and word of mouth ([sources](docs/research/real-rescue-practice.md)). The same family was posted many
times; others never posted at all. Nobody could say how many people were in which street, how deep the water was
there, or whether anyone was on the way. Volunteers drove to houses that had already emptied, while people who never
called were not checked.

## Try it in 60 seconds

Open the site. You get your own private demo room (nobody else sees your reports; Reset only resets yours).

1. **Play a victim.** Top left is a Hat Yai shophouse with the water at its modelled depth. Report on the phone below
   it, in Thai or English, by typing or by pressing **📞 Call** to talk to the agent through **Gemini Live**. Try:
   *"น้ำถึงเอวแล้ว อยู่กับแม่ แม่เดินไม่ได้ บ้านเลขที่ 52/9 ถนนเพชรเกษม ซอย 2"*. The agent asks only what is missing;
   under each answer you see what it understood, with your own words. The house scene becomes *your* house.
2. **Mention neighbours:** *"บ้านทางทิศตะวันออกมียายอยู่คนเดียว ทางทิศตะวันตกมีครอบครัว 4 คน"*. For each one the agent
   shows the satellite picture with that house outlined and asks "is it this one?". A house that already reported isn't
   counted twice; a new one is added as reported by a neighbour.
3. **Shelters:** if you can leave on your own, the agent offers the nearest shelter you can walk to (no stretch deeper
   than 0.5 m on the way), or says plainly that walking isn't safe now. Say *"ถึงแล้ว"* at the shelter and your house is
   marked empty for the teams.
4. **Press "Rain alert".** The flood model's response to 60 mm more rain tells each home how much its water will rise
   and when; homes with someone who can't walk are warned first.
5. **Open "Volunteer pages →"**: where help is missing (zones and ~350 m hotspots), the live feed of what the AI did
   with every message, a zone page, one family's whole case, and "Plan a trip". Post a plan and the families there are
   told; zones with a team coming are outlined on the map. After the visit, one tap: *picked up* or *nobody there*.
6. **Press "Play the flood"** to watch 21–28 Nov 2025 build up: water spreading from the hills and canals, reports
   arriving, duplicates merging, the picture sharpening.

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
  PL --> N["Notifier: plain Thai messages"]
  VP["Volunteer: one-line plan"] --> PL
  A --> BD["Board: zones, depth map,<br/>time-lapse, AI activity"]
```

| Step | What it does | Code |
|---|---|---|
| **Intake agent** | One question at a time, only what is missing: where, how many, who is vulnerable, how deep (with a concrete check: "above or below your door handle?"). Neighbours only when the person mentions them: their direction if missing, then a yes/no on the satellite picture. Offers a walkable shelter. Typed, held mic, or a Gemini Live call | [`intake.py`](api/v2/intake.py), [`live.py`](api/v2/live.py) |
| **Reader** | A language model turns any message into facts. Every fact must quote the person's exact words or it is dropped. Rules take over if the model is unavailable, and say so | [`ai.py`](api/v2/ai.py), [`reader.py`](api/v2/reader.py) |
| **Locator** | Address → Pinpoint → the Google Open Buildings outline under it. "The house to the east" → the nearest building in that compass sector (compass, because left and right depend on where you face) | [`geo.py`](api/v2/geo.py) |
| **Dedupe** | Counts households, not messages. Replies stay in their conversation; a relative's post merges only when exactly one nearby family has the same makeup; otherwise it is kept apart and counted as a range | [`pipeline.py`](api/v2/pipeline.py) |
| **Flood model** | Local-inertial shallow water (Bates et al. 2010) over the whole lower U-Tapao basin: IMERG rain, curve-number losses, Manning friction by land cover, canals, city drains that back up, Sadao inflow, Songkhla Lake. Street-level ground in dense blocks. Calibrated against the real gauge and news-reported depths | [`build_v2_basin_sim.py`](data/scripts/build_v2_basin_sim.py) |
| **Analyst** | Words → depth ranges with an error by wording and source. Optimal interpolation spreads each report's gap from the model (≈300 m, 12 h); where the model is dry but people report water, the water fills only the low ground. A report the model and its neighbours both contradict is marked doubtful, never deleted | [`assim.py`](api/v2/assim.py) |
| **Planner, Notifier** | Daily and alert check-ins; rain warnings with each home's expected rise from an extra-rain model run; "lost contact" after two missed checks; plan updates to every household in a zone; gaps such as "nobody plans medical help" | [`planner.py`](api/v2/planner.py), [`rain.py`](api/v2/rain.py) |
| **Shelters** | Real public buildings (OSM) that stay dry all week in the model and have no deep-water report nearby; a walk check along the way; check-in by the family, a team or shelter staff | [`shelters.py`](api/v2/shelters.py) |
| **Volunteer pages** | Where help is missing, live feed, zone, family case, plan a trip; exact addresses only for a team whose plan covers the zone | [`cases.py`](api/v2/cases.py), [`web/src/features/v2/volunteer`](web/src/features/v2/volunteer) |

**Which model:** Gemini reads every message (`REACHPOINT_LLM=gemini`, the default) and Gemini Live (`gemini-3.8-live`)
is the voice. During development the same reader also ran on Claude through the Claude Code CLI, to compare; every
reading is labelled with the model that made it.

## Measured, not claimed

[`docs/eval/v2-results.md`](docs/eval/v2-results.md), reproduced with `python api/scripts/eval_v2.py`, on the Hat Yai
scenario (real water data, synthetic people and messages, with deliberately wrong reports planted):

| Measure | Result | Target |
|---|---|---|
| Depth at a household, against the true depth there | 0.14 m mean error (median 0.12 m) | ≤ 0.2 m |
| Planted wrong reports flagged doubtful | 13 of 14 | ≥ 80% |
| Honest reports wrongly flagged | 3% | low |
| Two families wrongly merged into one | 1% | ≤ 3% |
| "The house to the east" matched to the exact building | 88% | ≥ 85% |

The scenario's "true" flood is the simulation plus local effects it can't know (blocked drains, pumps, smooth
differences), so these numbers show how well physics and reports combine, not field accuracy.

## Data

| Real | Synthetic |
|---|---|
| River gauge X.44 (RID), IMERG rain, Sentinel-1 flood extent, FABDEM terrain, ESA WorldCover (Earth Engine), Google Open Buildings outlines (30,086 in the city), OSM streets, canals and public buildings, news-reported depths (23–25 Nov), WorldPop and DOPA population | Every household, message, post, reply and volunteer plan. Bulletins are reconstructed from the real gauge readings and labelled as such |

Never enter real personal data.

## Honest limits

- **The flood model is a model.** Against the real data it runs about 1.2 m high at the gauge on average and drains too
  slowly, and downtown on 23 Nov it gives 0.3–0.7 m where people reported 0.5–2 m. Reports correct it where people
  talk; elsewhere it is labelled as the model.
- **Synthetic people.** The scenario was written by the team; the evaluation measures behaviour, not field accuracy.
- **Shelters are candidates,** not the official 2025 list; room is estimated from building size. The walk check uses
  the direct line, not the street network.
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
