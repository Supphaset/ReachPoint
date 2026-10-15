# ReachPoint v2: the flood picture that builds itself

Status: approved by Link on 15 Oct 2026 for the submission build. Earth to review.
Visual overview: https://claude.ai/artifact/AjYWwLJRyd62g6FozMQuoy (private; Link shares it).

## 1. What changes

ReachPoint stops being a dispatch tool. It becomes an information system that AI agents keep up to date by
themselves:

- **Victims** talk to an AI agent, by chat or voice. The agent asks only what is missing, asks about the neighbours
  and checks in again later.
- **Volunteers** post one line saying where and when they plan to go. They never enter measurements, take tasks or
  review data.
- **Everything else is automatic:** public posts, official bulletins, river gauge, rain and satellite passes come
  in by themselves, and agents turn them into one picture: households, people, water level by source, and plans.

Out of scope: task assignment, taking requests, handovers, crew–family calls, team codes, coverage confirmation,
photos, real SMS or phone calls. The old screens stay in the code but leave the navigation.

## 2. The judge experience (one page, `/`)

Left: the victim's phone. The judge chats or talks with the intake agent.
Right: the live board for Hat Yai city (area P-B, 13 zones):

1. Satellite map with zones coloured by the most likely water depth, household dots and the predicted spread.
2. A **time-lapse slider** from the first rain (18 Nov 2025) to day 3. Real gauge, rain and satellite dates;
   synthetic people. Charts: households known against the estimated affected total, and map certainty.
3. **Zone card** for the selected zone: people (estimate against reported), water by source with the most likely
   level and range, plans and gaps, and an AI summary with sources.
4. **AI activity**: each agent decision with its tool and evidence.
5. Demo clock buttons: +30 min, next day 07:00, rain alert, river rising, and "Flood the system".

The judge's report lands on the live map in front of them. Then a simulated plan arrives, and the judge's phone
shows "A boat team plans to come about 14:00". After that, a rain alert brings a safety check.

## 3. Data model (`api/v2/model.py`)

| Thing | Key fields |
|---|---|
| Building | id, centroid, outline, groundM (FABDEM), zoneId, nearest street and side |
| Household | id, buildingId, zoneId, people (count, elderly, children, cannotWalk), needs, status (open, confirmedSafe, lostContact), reportIds, firstHand |
| Message | id, channel (chat, voice, post, bulletin, safetyReply), at, text, about (self, neighbour, area), householdId |
| Fact | messageId, field, value, quote (exact words), confidence |
| DepthObservation | buildingId, at, loM, hiM, sourceKind, messageId, weight, label (unconfirmed, confirmed, doubtful) |
| Plan | team, vehicle, seats, zoneIds (in order), eta, offers, postedAt, updates |
| Outbound | householdId, at, kind (followUp, safetyCheck, earlyWarning, planUpdate, rainAlert, riverAlert, morning), text, replyId |
| Activity | at, agent, summary, tool, evidence ids |

Every number on the board links back to facts, observations or estimates.

## 4. Pipeline and agents

A supervisor runs on the demo clock: every 15 simulated minutes, and on each new message. It runs these steps
in order and logs each decision to Activity.

1. **Intake** (live chat or voice). It asks one question at a time, only for missing critical facts: location,
   people, vulnerable people, water depth, then neighbours (left, right, across, behind). It skips the neighbour
   questions when the case is life-threatening. Every fact keeps its quote.
2. **Reader** turns public posts and bulletins into the same facts, in batch. It spots forwarded or old text.
3. **Locator** finds the address with Pinpoint, snaps the point to the nearest building outline, and turns
   neighbour words into a building. It uses the street direction (OSM) to define left, right, across and behind,
   as seen from the door. Gemini picks a building from the candidates and gives a reason; rules come first.
4. **Dedupe** decides whether this is the same household. A phone match or the same building is sure, unless the
   names or descriptions clearly differ. Otherwise Gemini compares the two. Results: sure (merge), probably (one
   household, with the count shown as a range) or different.
5. **Analyst**
   - turns words into a depth range ("knee-deep" ≈ 0.4–0.6 m);
   - computes water-surface height (groundM + depth);
   - combines observations per zone with a weighted median, using confidence × freshness as the weights, and
     reports the 25–75% range;
   - flags outliers, works out the depth at every building, and the trend in cm/h;
   - explains disagreements between sources, such as satellite "dry" against reports "chest-deep" in built-up
     blocks;
   - predicts the spread from the gauge trend, the terrain and rain.
6. **Planner** decides whom to ask what. It sends a concrete check question when a report is vague or doubtful,
   asks people at the edges of quiet zones (high estimate, few reports), and warns vulnerable households in the
   predicted path first.
7. **Notifier** writes every outbound message in plain Thai or English. It never reveals one household's details
   to another.

The Gemini calls are extraction, building choice, dedupe comparison, consistency check, zone summary, plan line
and messages. Each has a deterministic rule fallback, so the demo never stalls, and fallbacks are labelled.

## 5. Confidence and confirmation

Each depth observation gets a weight from these rules:

| Rule | Effect |
|---|---|
| First-hand | 1.0; neighbour 0.7; public post 0.5; forwarded or old post 0.2 |
| Location precision | Pinpoint building 1.0; landmark 0.6; area only 0.3 |
| Freshness | Half-life 3 hours |
| Self-consistency | Gemini flags contradictions, ×0.5 |
| Possible here | If groundM is more than 2 m above the zone's water surface and the report is deep, it's doubtful |
| Agreement | Outside the zone's 25–75% water-surface range by more than 0.5 m makes it doubtful, and the planner asks a check question |

Labels: **Unconfirmed** means one source. **Confirmed** means first-hand plus an independent source within range.
**Doubtful** means it conflicts with most evidence. Reports are never discarded.

Safety rule: an urgent request is shown at once, marked unconfirmed. Checks never delay it.

## 6. Scenario: Hat Yai, 18–30 Nov 2025

`data/scripts/build_v2_scenario.py` builds `data/hy-2025-11/v2-scenario.json` with a fixed seed. Inputs:

- **Real:** gauge X.44, rain (IMERG), satellite extents (23 and 29 Nov), zones and population estimate,
  building outlines, terrain.
- **Synthetic:**
  - about 700 messages across 4 channels: chat, voice, posts, safety replies;
  - about 230 households on real buildings;
  - the true water surface per zone per hour, shaped by the gauge;
  - duplicates, neighbour reports, forwarded posts and planted wrong reports;
  - bulletins written from the real gauge readings, labelled as reconstructed;
  - volunteer plans.

The background messages are read by Gemini once, in a batch run, and the facts are cached in the scenario file.
The judge's own messages are read live. The scenario also keeps its ground truth, which the evaluation uses.

## 7. Evaluation (`api/scripts/eval_v2.py`)

The run uses the scenario's ground truth.

| Measure | Target |
|---|---|
| Facts with a correct supporting quote | ≥ 95% |
| Duplicates merged correctly | ≥ 90% |
| Two families wrongly merged | ≤ 3% |
| Neighbour words matched to the right building | ≥ 85% |
| Depth from words within one band | ≥ 85% |
| Planted wrong reports flagged as doubtful | ≥ 80% |
| Most likely level against the true level | Within 0.2 m |

Results go in `docs/eval/v2-results.md`, the README and the deck.

## 8. API (new, under `/api/v2`)

| Route | Purpose |
|---|---|
| `GET /api/v2/state?at=ISO` | Board state at a time: zones, households, levels, plans, activity |
| `GET /api/v2/timeline` | Time-lapse steps with summary numbers |
| `POST /api/v2/chat/sessions`, `POST /api/v2/chat/sessions/{id}/turn` | Intake agent |
| `GET /api/v2/me/{token}` | The victim's status page and inbox |
| `POST /api/v2/plans` | Volunteer plan line |
| `POST /api/v2/clock` | Advance, next morning, rain alert, river rising, flood the system |

Rooms (`X-Demo-Room`) keep each judge's copy separate, as before.

## 9. Build order (deadline 18 Oct)

1. Spec; data prep (buildings + ground from Earth Engine); scenario generator; level fusion and confidence, with
   tests.
2. State and timeline API; board with time-lapse, zone card and activity.
3. Intake agent (chat, then voice), Locator, Dedupe, neighbour flow; the judge page.
4. Supervisor, Planner and Notifier: follow-ups, checks, early warnings, plan updates, lost contact.
5. Plan line; "Flood the system"; batch Gemini run on the scenario; evaluation.
6. Deploy, video, deck.

Later: Google Flood Hub and Weather API as prediction inputs (if access), situation reports and broadcasts in
Thai, English and Burmese.

## 10. Open items

- Earth's `main` (caller schema, coordinator desk) diverged from `claude/integrate-call` in the intake files.
  v2 uses its own intake module. The merge is to be decided with Earth.
- Bulletins are reconstructed from the real gauge readings until we find the real November 2025 notices.
