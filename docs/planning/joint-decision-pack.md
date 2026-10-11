# ReachPoint — joint technical decision pack

Date: 2026-10-11 (Asia/Bangkok). Status: **Working document behind [decision 0009](../decisions/0009-implementation-start-and-technical-direction.md).** The user's answers are recorded in the next section; 0009 is the authoritative summary. Everything else here (contract shapes, transitions, plan) stays **proposed** until both humans review it. Research was read on 2026-10-11 from organizer pages, Google documentation and news reports; recheck mutable facts before relying on them.

> **Update later on 2026-10-11 (read first).** Three later user decisions supersede parts of this pack:
> 1. **No real phone line** in the prototype (eng R21). A browser call screen represents a phone call. B4, the "Thai number" row, §5.2/§5.2a, the Twilio items and the phone gate are kept only as history. See the [0009 amendments](../decisions/0009-implementation-start-and-technical-direction.md#amendments-user-decisions-later-on-2026-10-11).
> 2. **Pull model (21A):** no offers. Reviewed cases go to shared priority lists, and the first capable team to take a family group wins. "offered", offer expiry and `respondToMissionOffer` in §3, §4.2, §6 and §7 are replaced by `publishListing` / `claimListing`, with allocations starting at `accepted`.
> 3. **Eng re-check decisions D1–D14** (family groups, job endings, outdated-case checks, colour-then-distance ordering, shared open lists, server-checked resident messages, coordinator-only solver): see the [design doc](../designs/resource-split-and-live-loop.md) and the [real rescue practice research](../research/real-rescue-practice.md).

Labels: **[ACCEPTED]** = already a recorded human decision in the repo. **[PROPOSED]** = recommendation in this pack or an existing proposal in the repo. **[OPEN]** = unresolved and needs a human.

---

## Human answers recorded 2026-10-11 (one partner; friend's confirmation pending)

| Topic | Answer | Effect / follow-up |
|---|---|---|
| B1 Implementation | **Authorized from 12 Oct** under the §6 timebox | Record in `0009`. Becomes joint once the friend confirms |
| B2 Stack | **A: FastAPI on Cloud Run + Firestore + React on Firebase Hosting** | Map provider, auth details and Gemini route are still open (Group 2) |
| B4 Phone | ~~Connect the Thai number you already have if possible; otherwise browser voice for now~~ **Superseded: no real phone line in the prototype; a browser call screen represents a call (R21)** | See §5.2a. Browser voice is an **interim, disclosed** state. R2 isn't marked done until a real call works, or both of you sign a scope revision |
| Map + AI route | **Google Maps JS API + Gemini via Vertex AI** | Restricted Maps key (HTTP referrer + API restriction); Gemini only server-side through the Cloud Run service account |
| B6 GCP project layout | **Accepted recommendation (2026-10-11):** one shared project **`reachpoint-main`**, owned by the **friend**, user as Editor. It holds Cloud Run, Firestore, Firebase Auth/Hosting, Vertex AI/Gemini, Maps key, Secret Manager and the deployed demo. **User's sandbox project** holds Earth Engine (noncommercial) + Gemini prompt experiments; its output is GeoJSON committed to `data/` or uploaded to main's Cloud Storage, so **nothing is merged later**. Optional friend sandbox for phone/Live spikes | `reachpoint-main` must exist by **Mon 12 Oct evening** (CP0). Budget alert on **every** project. No keys or service-account files in Git. **Spend cap amount and Twilio payer are still open.** Friend must confirm owning the main project |
| Thai number | **AIS monthly (postpaid) SIM** (user unsure of details) | Try R-a forwarding. Call 1175 first; §5.2a |
| Flood AOI | **Superseded later the same day:** use **past** events. **Hat Yai, Nov 2025 = main scenario; Bangkok, Sep 2026 = second package** | §5.1b. P-A/P-B/P-C, teams, CALL-01/C-01/M-01 all sit in Hat Yai. Bangkok shows map + area briefing only (eastern-fringe S1 extent + cited reported-street-flood points), with no synthetic households, calls or teams |
| B5 Flood | **Real satellite extent from the start** | **Revises 0005's "one bounded fictional locality".** Needs a 0009 entry: real geography + real historical extent; operational records (households, teams, calls) stay synthetic and labeled. Event/AOI choice is open |

---

## 0. The time constraint shapes everything

| Fact | Source | Consequence |
|---|---|---|
| Prototype deadline **18 Oct 2026**, exact time/zone not published | aibuildercup.com, terms | **7 days from today.** Plan to submit by the evening of **17 Oct, Bangkok time**, and treat 18 Oct as a buffer. |
| Needed: live URL on **Cloud Run or Firebase**, **public GitHub repo**, **video under 3 min**, **PDF deck** (architecture + business case), all in English | terms, themes, FAQ | You need a deployed URL early. Don't plan to deploy only at the end. |
| Code and assets must be **fresh, made during the event** | terms | No code exists yet, so this is fine. Don't copy code from the old discussion prototype. |
| Must use **Gemini/Gemma or a Google agent platform** and run on Google Cloud | themes, FAQ | The AI has to be real and visible, not a side feature. |
| Judging: **Gen AI technical merit 40%**, problem/impact 25%, innovation 25%, UX 10% | themes, FAQ, terms | See §0.1. |
| Roster registration closed **today (11 Oct)** | terms | **[OPEN] Confirm today that you're both registered and eligible (21+, not students, JAPAC residents).** |
| Implementation is **not yet authorized** | AGENTS.md, 0005–0007 | Blocker B1 below. |

### 0.1 What the rubric means for ReachPoint [PROPOSED]

The repo's invariants are correct and they set you apart: AI proposes, humans review, deterministic rules own quantities and states. But at 40%, the judges need to *see* substantial Gemini work. That can happen without breaking any invariant:

| AI feature (all proposal-only) | Google tool | Rubric hit | Owner |
|---|---|---|---|
| **Thai voice intake agent on a real phone line.** It talks, clarifies, and calls tools that create *proposed events* | Gemini Live API (`gemini-3.1-flash-live` family; verify the current model ID) on Cloud Run | Tech 40, Innovation 25 | Friend |
| **Evidence-linked extraction.** Report → typed proposed events, each citing the transcript span it came from | Gemini structured output (Flash) | Tech 40 | Friend |
| **Reconciliation suggestions.** "This call probably concerns C-01 (already counted in P-B's 24)", with reasons; a human confirms | Gemini + deterministic candidate search | Tech 40, Impact | Friend |
| **Area briefing explainer.** Prose explaining *why* an area needs attention, written only from computed numbers, with record IDs cited. Never produces its own numbers | Gemini Flash | Tech 40, UX | You |
| **Change-impact brief.** When S1 is lost, drafts the brief-v2 text and lists affected records for the coordinator to approve | Gemini Flash | Innovation | You (text) / Friend (trigger) |
| **(Stretch) Real flood extent** for a past event: Sentinel-1 change detection, precomputed | Earth Engine | "Best use of Google Cloud AI tools" award, Impact | You |

Guard against invented AI output in every feature: validate the schema and the referenced IDs, show the source span, and keep "saved ≠ approved".

---

## 1. What's settled, what's proposed, what blocks you

### Already settled [ACCEPTED]
- Theme Sustainability & Social Impact. Name ReachPoint. Public repo (0008).
- Prototype scope v1 (0005): five experiences; P-A/P-B/P-C; T-R/T-S/T-M; one relief mission (PL-A); one emergency (CALL-01 → C-01 → M-01/M-M); resident timing is a core feature.
- Split (0006): you own the volunteer workspace and flood map; your friend owns resident and coordinator, intake, reconciliation and database.
- Invariants (requirements.md): need, review, commitment, progress, receipt and care stay separate. Unknown ≠ zero. No double-counting. No AI clinical triage. No fabricated depth or routes.
- R2: ~~a genuine inbound phone call~~. **Deferred beyond the prototype by the user (2026-10-11)**; the browser call screen stands in for it.

### Proposed in the repo, not yet accepted
- 0007 logical architecture: one shared backend, derived views, AI with no direct write path.
- Draft contract v1: operation names, `submissionId`/`expectedVersion`, error codes.
- Detailed split: you own team mission/update and planning rules; your friend owns resident status, routine-plan review and state enforcement. **Your message today restates exactly this. If your friend agrees too, record it as accepted in 0009.**

### The six blockers (decide in this order)
| # | Decision | Why it blocks | Recommendation |
|---|---|---|---|
| B1 | **Authorize implementation and the 7-day timebox** | AGENTS.md forbids any build | Authorize from 12 Oct, under the checkpoint plan in §6 |
| B2 | **Stack** (frontend/backend/DB/auth/hosting) | Both of you scaffold on day 1 | Option A in §2 |
| B3 | **Freeze contract v1.0**: collections, IDs, state fields | Lets you both build in parallel against fixtures | §3–§4 as written, after a 30-min joint review |
| B4 | **Phone gate**: provider, number country, spend owner | Account setup has lead time | Twilio paid account with a **US number** + Gemini Live bridge; §5.2 |
| B5 | **Flood data**: synthetic fixture vs real historical extent | Determines your first two days | Synthetic fixture first, Earth Engine as a stretch; §5.1 |
| B6 | **GCP project, billing owner and spend cap; Gemini route** | Nothing deploys without these | One project owned by one of you, both as editors, budget alert; Gemini through **Vertex AI** (one IAM path, no API keys in clients) |

---

## 2. Frontend / backend / database options [PROPOSED]

You're two data scientists with 7 days, so pick for speed, Python familiarity and visible Google usage.

| | **A. Python API + Firestore + React (recommended)** | B. All-Firebase TypeScript | C. All-Python UI (Streamlit/Gradio) |
|---|---|---|---|
| Frontend | React + Vite (TS), on Firebase Hosting | Next.js on Firebase App Hosting | Streamlit on Cloud Run |
| Backend | **FastAPI on Cloud Run**: REST actions, the phone WebSocket bridge, Gemini calls, rule engine | Cloud Functions + Firebase AI Logic | Inside the Streamlit app |
| DB | **Firestore**: writes go only through the server; clients subscribe to derived view docs | Firestore, or SQL Connect (Cloud SQL) | Firestore |
| Realtime refresh | Firestore listeners on view docs (settles the "polling vs subscription" question) | Same | Weak (reruns) |
| Gemini | `google-genai` SDK on Vertex AI, server-side | AI Logic in the client is risky for "AI never writes state" | Server-side |
| Phone bridge | Same FastAPI service (WebSocket) | Still needs a Cloud Run service | Separate service anyway |
| Earth Engine | Python EE API, matches your skills | Awkward | Fine |
| Pros | Python everywhere it counts; one backend owns all state transitions; clean "derived permitted views" story for the deck | Least backend code; one language | Fastest to first screen |
| Cons | Two deploy targets (Hosting + Run); the frontend still needs React | Rules and functions get complex for versioned transitions; phone forces Cloud Run anyway | Poor map and multi-role UX (hurts the 10% UX score and the Best UI/UX award); hard to show 4 role views |

Why Firestore over Cloud SQL for this prototype: no always-on instance cost, no migration tooling, and realtime listeners for free. Transactions give you `expectedVersion` checks, and a doc keyed by `submissionId` gives you idempotency. The cost is no PostGIS: area geometry lives in GeoJSON assets (Cloud Storage or static), not in DB queries. That's fine for three areas.

**Map:** [OPEN] Google Maps JS API (Google-native, needs a restricted key and billing) vs MapLibre GL + OSM tiles (no key, but must follow the tile-usage policy). Leaning Google Maps for judging fit. Either way, the list/detail view must keep working when tiles fail (accepted requirement).

**Auth (demo-grade):** Firebase Auth with **4 seeded test accounts** that carry custom-claim roles (`coordinator`, `team_leader:T-R`, `team_leader:T-S`, `qualified_reviewer_fixture`). The resident accesses status through an **unguessable status link token** (`views/residentStatus/{token}`), with no lookup by phone number. Firestore rules let each role read only its own view docs. All writes are denied to clients and go through the API.

**Repo layout (proposed):** a monorepo with `web/` (React; one app with role-based routes, so the two of you share components and auth), `api/` (FastAPI), `contract/` (JSON Schemas + fixtures, the single source both of you test against), `data/` (your source package), `docs/`. File ownership: you own `web/src/volunteer/**`, `web/src/map/**`, `data/**`, `api/rules/planning.py`. Your friend owns `web/src/desk/**`, `web/src/resident/**`, `api/**` (except planning.py). Both own `contract/**`, and changes there need both to review.

---

## 3. Shared data contract v1.0 (exact proposal)

Conventions (from draft v1, kept): ISO-8601 UTC strings; displayed in Asia/Bangkok. `null` + `…Reason` for unknown, never 0. Every authoritative doc has `version` (int, +1 per change), `updatedAt` and `updatedBy` (actor id). Every doc has `dataMode: "synthetic"`. Phone numbers are never IDs.

### 3.1 Collections and owners

| Collection | Meaning | Writer (via API only) | Meaning-owner |
|---|---|---|---|
| `areas/{areaId}` | P-A/P-B/P-C, boundaryVersion, landmark list (L1…L3) | seed script | **You** |
| `evidence/{evidenceId}` | typed flood/exposure items (EXT-A, DEP-A, POP-A…) | `submitSourcePackage` | **You** |
| `reports/{reportId}` | raw incoming items: `channel` ∈ phone, chat, field_observation, team_report | intake, team UI | Friend |
| `proposedEvents/{eventId}` | AI or human proposals linked to a report span | AI pipeline, desk | Friend |
| `cases/{caseId}` | household/request case; identity, location, people basis | review actions | Friend |
| `assistance/{assistanceId}` | **one doc per assistance type per case** (evacuation, medical, supplies) | review, mission rules | Friend |
| `teams/{teamId}`, `resources/{resourceId}` | capability, availability, capacity basis | seed, `submitTeamUpdate`, review | **You** (inputs) / Friend (enforcement) |
| `proposals/{proposalId}` | routine plans (PL-A) | `submitMissionProposal` | **You** |
| `missions/{missionId}` (+ `briefs/{n}`) | offers/accepted tasks; arrival windows; brief versions | desk offers; team actions | Friend (transitions) / You (team actions UI) |
| `submissions/{submissionId}` | idempotency ledger: hash + stored result | API middleware | Friend |
| `history/{historyId}` | append-only audit of every applied change | rules engine | Friend |
| `views/areaBriefing/{areaId}` | derived; schema already in draft v1 | rules engine | **You** (calculation) |
| `views/teamMissions/{teamId}` | derived own-team list | rules engine | You (shape) |
| `views/desk/{caseId}` | derived coordinator case view | rules engine | Friend |
| `views/residentStatus/{token}` | derived own-request status | rules engine | Friend |

### 3.2 Synthetic records for the emergency (times = Bangkok 10:10 → 03:10Z)

**Report — CALL-01** (friend's intake writes this)
```json
{
  "reportId": "CALL-01", "dataMode": "synthetic", "version": 1,
  "channel": "phone", "language": "th",
  "receivedAt": "2026-10-11T03:10:00Z",
  "callerRef": "CALLER-ANON-7",
  "transcript": [
    {"spanId": "s1", "speaker": "caller", "text": "ตอนนี้ครอบครัวเราอยู่ที่อาคารชุมชน มีสามคน"},
    {"spanId": "s2", "speaker": "caller", "text": "คนหนึ่งต้องการความช่วยเหลือทางการแพทย์"},
    {"spanId": "s3", "speaker": "caller", "text": "เพื่อนบ้านยังอยู่ที่เดิม"}
  ],
  "translation": {"lang": "en", "label": "machine_translation_unreviewed",
    "spans": {"s1": "Our household is at the community building now. There are three of us.",
              "s2": "One needs medical help.", "s3": "The neighbor stayed."}},
  "recording": null, "recordingReason": "not_retained_by_design",
  "processingState": "proposals_ready"
}
```

**Proposed events** (from Gemini; nothing is authoritative yet)
```json
[
  {"eventId": "PE-01", "reportId": "CALL-01", "type": "location_update", "state": "pending",
   "proposed": {"landmarkId": "L3", "label": "community building", "movedAt": null, "movedAtReason": "not_stated"},
   "evidenceSpans": ["s1"], "proposer": "ai:gemini", "confidenceNote": "landmark name matched catalogue entry L3"},
  {"eventId": "PE-02", "reportId": "CALL-01", "type": "assistance_request", "state": "pending",
   "proposed": {"assistanceType": "evacuation_transport", "people": 3, "peopleBasis": "caller_stated"},
   "evidenceSpans": ["s1"], "proposer": "ai:gemini"},
  {"eventId": "PE-03", "reportId": "CALL-01", "type": "assistance_request", "state": "pending",
   "proposed": {"assistanceType": "medical", "people": 1, "peopleBasis": "caller_stated", "clinicalDetail": null},
   "evidenceSpans": ["s2"], "proposer": "ai:gemini"},
  {"eventId": "PE-04", "reportId": "CALL-01", "type": "case_association", "state": "pending",
   "proposed": {"caseId": "C-01", "reason": "same household size, area P-B, landmark proximity; already within P-B reviewed demand 24"},
   "evidenceSpans": ["s1"], "proposer": "ai:gemini"},
  {"eventId": "PE-05", "reportId": "CALL-01", "type": "possible_other_household", "state": "pending",
   "proposed": {"note": "neighbor remained at prior location; identity unknown"},
   "evidenceSpans": ["s3"], "proposer": "ai:gemini"}
]
```

**Case — C-01 after coordinator review (v3)**
```json
{
  "caseId": "C-01", "version": 3, "dataMode": "synthetic", "areaId": "P-B",
  "identity": {"state": "provisional", "householdRef": "HH-B-017"},
  "people": {"count": 3, "basis": "caller_stated_reviewed", "countedIn": ["P-B:assisted_evacuation_demand:v1"]},
  "currentLocation": {"landmarkId": "L3", "source": "CALL-01", "observedAt": null, "accuracy": "landmark", "reviewState": "reviewed"},
  "plannedPickup": {"landmarkId": "L3", "reviewState": "under_review"},
  "assistanceIds": ["AS-01-EVAC", "AS-01-MED"],
  "reportIds": ["CALL-01"],
  "openQuestions": ["Time of move unknown", "Neighbor identity unresolved (PE-05 kept pending)"],
  "owner": "coordinator:demo-1",
  "updatedAt": "2026-10-11T03:15:00Z"
}
```

**Assistance — each state dimension is its own field, never one combined enum**
```json
{
  "assistanceId": "AS-01-EVAC", "caseId": "C-01", "type": "evacuation_transport", "version": 4,
  "review":              {"state": "validated", "by": "coordinator:demo-1", "at": "2026-10-11T03:15:00Z"},
  "qualifiedAssessment": {"state": "assessed_fixture", "ref": "Q-01", "label": "FICTIONAL qualified review"},
  "allocation":          {"state": "accepted", "missionId": "M-01", "teamId": "T-S", "acceptedAt": "2026-10-11T03:20:00Z"},
  "progress":            {"state": "preparing", "reportedBy": "team:T-S", "reportedAt": "2026-10-11T03:20:00Z"},
  "arrivalWindow":       {"state": "current", "start": "2026-10-11T06:00:00Z", "end": "2026-10-11T07:00:00Z",
                          "basis": "team_estimate", "source": "team:T-S", "missionVersion": 2, "setAt": "2026-10-11T03:20:00Z"},
  "nextStatusUpdate":    null,
  "outcome":             {"state": "unconfirmed"}
}
```
```json
{
  "assistanceId": "AS-01-MED", "caseId": "C-01", "type": "medical", "version": 3,
  "review":              {"state": "validated", "by": "coordinator:demo-1"},
  "qualifiedAssessment": {"state": "assessed_fixture", "ref": "Q-01", "requiredCapability": "medical_team", "label": "FICTIONAL qualified review"},
  "allocation":          {"state": "offered", "missionId": "M-M", "teamId": "T-M"},
  "progress":            {"state": "not_started"},
  "arrivalWindow":       {"state": "none", "reason": "no_team_acceptance"},
  "nextStatusUpdate":    {"at": "2026-10-11T04:00:00Z", "owner": "coordinator:demo-1"},
  "outcome":             {"state": "unconfirmed"}
}
```

**Mission — M-01 after acceptance**
```json
{
  "missionId": "M-01", "version": 2, "kind": "emergency_transport", "dataMode": "synthetic",
  "assistanceIds": ["AS-01-EVAC"], "teamId": "T-S", "resourceIds": ["S1"],
  "state": "accepted",
  "checks": {"capacity": "passed:OP-01", "access": "passed:OP-01", "receivingDestination": "passed:D1"},
  "brief": {"currentVersion": 1, "acknowledgedVersion": 1, "acknowledgedAt": "2026-10-11T03:20:30Z"},
  "pickup": {"landmarkId": "L3"}, "destinationId": "D1",
  "windows": [{"windowId": "W-01", "state": "current", "start": "2026-10-11T06:00:00Z", "end": "2026-10-11T07:00:00Z", "basis": "team_estimate"}],
  "hold": null
}
```

**Team report — TEAM-01 (your team UI submits this; shape already in draft v1)**: `reportType: "resource_unavailable"`, `resourceId: "S1"`, `missionId: "M-01"`, `expectedVersion: 2`, `submissionId: "SUB-TEAM-01"`.

**Resident status view — what the resident sees after the hold** (derived; never hand-edited)
```json
{
  "token": "rs_9f2c…", "caseRef": "C-01", "generatedAt": "2026-10-11T03:32:00Z", "inputVersions": {"case": 3, "AS-01-EVAC": 6, "AS-01-MED": 3, "M-01": 3},
  "items": [
    {"type": "evacuation_transport", "headline": "Your transport is on hold. A new time is not known yet.",
     "team": "Rescue team T-S", "window": null, "withdrawnWindow": {"start": "2026-10-11T06:00:00Z", "end": "2026-10-11T07:00:00Z", "withdrawnAt": "2026-10-11T03:32:00Z"},
     "nextUpdate": {"at": "2026-10-11T04:00:00Z", "owner": "Coordinator desk", "label": "status update, not arrival"}},
    {"type": "medical", "headline": "We are seeking a suitable medical team; arrival time is not confirmed.",
     "team": null, "window": null, "nextUpdate": {"at": "2026-10-11T04:00:00Z", "owner": "Coordinator desk"}}
  ]
}
```

**History entry** (one per applied change)
```json
{"historyId": "H-0042", "at": "2026-10-11T03:32:00Z", "actor": "coordinator:demo-1", "submissionId": "SUB-DESK-0042",
 "action": "review_team_report", "target": "TEAM-01",
 "changes": [{"doc": "missions/M-01", "from": {"state": "accepted", "version": 2}, "to": {"state": "held", "version": 3}},
             {"doc": "assistance/AS-01-EVAC", "field": "arrivalWindow.state", "from": "current", "to": "withdrawn"},
             {"doc": "resources/S1", "field": "availability", "from": "available", "to": "unavailable"}]}
```

---

## 4. Ownership, permissions and state transitions [PROPOSED]

### 4.1 Who may read what
| Role | Reads | Never sees |
|---|---|---|
| coordinator | all `views/desk`, reports+transcripts, proposedEvents, all missions, area briefings | — |
| team_leader (T-x) | all `views/areaBriefing` (aggregates), own `views/teamMissions/T-x`, own mission pickup/destination | transcripts, medical narrative, other teams' missions, phone/caller refs |
| resident (token) | own `views/residentStatus/{token}` only | anything else; no lookup by phone |
| qualified_reviewer_fixture | assigned case's operational facts; writes the Q-01 fixture | — |
| ai (service) | minimum context for one report or area | write access to anything except `proposedEvents` |

### 4.2 Transitions (rules engine; every one checks role + `expectedVersion` + `submissionId`)
| Record.field | From → To | Actor | Guard / side effects |
|---|---|---|---|
| proposedEvent.state | pending → approved / edited_approved / rejected | coordinator | Approval applies the change to case/assistance and writes history. Rejection changes nothing else |
| assistance.review | reported → validated / needs_clarification | coordinator | A suspected emergency stays visible in both states |
| assistance.qualifiedAssessment | not_required / pending → assessed_fixture | qualified_reviewer_fixture | Labeled FICTIONAL. The coordinator can't set it |
| listing | none → open (rev 1) | coordinator (review approval publishes) | Case × assistance type with household groups and `lastConfirmedAt`; appears in the open list for its assistance type. **Resident still sees "seeking team"** |
| listing.needRevision | n → n+1 | coordinator (correction, withdrawal, group split) | Updated in the same transaction as the review change |
| allocation | none → accepted | team_leader (own team, Available, capable) | `claimListing` on whole groups with the revision it saw; one transaction over listing + resource + team; `ALREADY_TAKEN` / `NOT_ENOUGH_CAPACITY` / `NEED_CHANGED`. Acceptance ≠ acknowledgment ≠ arrival |
| allocation | accepted/in progress → closed (done / already_left / not_found / needs_more_help / handed_back) | team_leader, or coordinator for hand-back | Only unfinished groups are relisted (rev n+1); late updates on a closed allocation return `ALLOCATION_CLOSED`; "delivered, not confirmed" supplies need the coordinator |
| mission.brief.acknowledgedVersion | n-1 → n | team_leader | Exactly the current version; a new brief never inherits the ack |
| arrivalWindow | none → current | team_leader on an accepted allocation | Only now does the resident see a window, **per group** |
| progress | not_started → preparing → en_route_reported → on_scene_reported → completed_reported | team_leader | **Never sets outcome** |
| resource.availability | available → unavailable_reported | team_leader (report) | Creates desk attention; nothing else changes yet |
| resource.availability + mission.state + window | unavailable_reported → unavailable; accepted → held; current → withdrawn | coordinator (reviews report) | Linked missions only; nextStatusUpdate set with owner; brief v(n+1) saved with ack pending |
| outcome | unconfirmed → receipt_confirmed / care_handover_confirmed | coordinator, with a separate confirmation | Never inferred from progress |
| proposal (routine) | draft → submitted → approved_as_mission / returned | team_leader → coordinator | A draft never changes coverage or stock |

---

## 5. Feasibility

### 5.1 Flood data

> Superseded by the user's choice (0009 D6): real past events, Hat Yai main and Bangkok second, see §5.1b. The option table is kept for the reasoning.
| Option | What | Effort (you) | Honesty label | Recommendation |
|---|---|---|---|---|
| F1 Synthetic package | Hand-made GeoJSON for 3 fictional areas + EXT/DEP/POP items exactly as in the fixture | ~0.5 day | "Synthetic demonstration data" | **Do first.** The contract and every screen depend on it |
| F2 Real historical extent | Earth Engine Sentinel-1 before/after change detection over a real past event (e.g. Hat Yai, Nov 2025), exported once to GeoJSON; Open Buildings counts and WorldPop exposure per area | 1–1.5 days, precomputed offline; the app makes no live EE calls | "Real satellite extent from {date}; operational records synthetic" | **Stretch, decide at Checkpoint 2.** Needs a scope change: the locality is no longer fictional (0005 says "fictional locality") |
| F3 Live feeds (GISTDA, ThaiWater, Flood Hub API) | Live integration | Unknown; Flood Hub needs waitlist approval | — | **Not in 7 days.** Mention as roadmap in the deck |

### 5.1a Candidate current events (superseded: past events chosen, see §5.1b) (research 2026-10-11; figures are dated snapshots from news reports of official statements)

**Current event: central/eastern Thailand + Bangkok, late Sep – Oct 2026.**
- DDPM, 10 Oct 06:00: flooding in **21 provinces + Bangkok**, about 1.14 M households / 3.16 M people, 53 deaths. Highest death tolls: Prachin Buri 23, Samut Prakan 9, Bangkok 4. Bangkok has 329k affected households; water remains in 97 communities across six eastern districts (Min Buri, Nong Chok, Prawet, Saphan Sung, Lat Krabang, Bueng Kum).
- GISTDA satellite analysis for 28 Sep – 4 Oct found inundation in 45 provinces (about 5.12 M rai). Sentinel-2C imagery from 7 Oct covers Ayutthaya, Ang Thong and Suphan Buri. More heavy rain is forecast around 10–12 Oct.
- I found **no Copernicus EMS or International Charter activation** for this event, so there's no ready-made reference product. You'd compute your own extent from Sentinel-1.

**Past event: Hat Yai / Songkhla, Nov 2025.**
- Rainfall: 335 mm on 21 Nov, about 630 mm over 19–21 Nov. Water entered the city centre on 23 Nov.
- GISTDA released Sentinel-1A + HAND depth estimates on 24 Nov. The International Charter was activated (#1004, 25 Nov 2025).

| AOI | Satellite fit | Story fit | Caveat | Proposed role |
|---|---|---|---|---|
| **Prachin Buri** (current) | Good. Largely rural/peri-urban, where SAR change detection works well | Highest death toll; on the Bangkok approach from the east | Need to choose sub-district boundaries for P-A/P-B/P-C | **Primary demo locality** (recommended) |
| Ayutthaya / Ang Thong (current) | Good. Riverine plain; Sentinel-2C 7 Oct optical available as a cross-check | Classic Chao Phraya flood | Many existing maps, so less novel | Alternative primary |
| **Bangkok east** (Min Buri / Nong Chok / Lat Krabang) | **Weak in dense urban cores.** SAR misses water between buildings (double-bounce); fine over the paddy/suburban fringe | Strongest "Bangkok" recognition | Must show uncertainty; no claim of complete urban extent | Inset or second planning area, with an explicit "urban under-detection" label |
| **Hat Yai** (Nov 2025) | Urban-core under-detection again; GISTDA itself used HAND for depth | Extreme event, good for the deck's problem framing | Past event; no depth from you (no own depth model per invariants) | **Second package: map/briefing replay only**, no operational records. Timebox to 0.5 day |

### 5.1b Chosen: two past events (human instruction 2026-10-11)

| | **Bangkok, 24–28 Sep 2026** | **Hat Yai / Songkhla, 19–29 Nov 2025** |
|---|---|---|
| What happened | About 300 mm in about 48 h from 24 Sep. Mainly **rain that drainage couldn't clear**, not river overflow. Disaster declared in all 50 districts on 26 Sep. About 52k households affected, about 4,900 people in shelters | 335 mm on 21 Nov, about 630 mm over 72 h. Runoff surged into the city centre on 23 Nov; GISTDA mapped 2–3 m (locally > 4 m) on 24 Nov. International Charter activation #1004 |
| Worst areas | East: Lat Krabang (worst), Bang Kapi, Khan Na Yao, Sai Mai, Suan Luang, Saphan Sung, Lak Si; first declarations in Nong Chok/Suan Luang/Khan Na Yao. Road flooding at 80+ points (e.g. Ramkhamhaeng 25–30 cm); waist-deep in places. Water lingered in eastern fringe communities into October | Hat Yai city + surrounding districts |
| **Sentinel-1 fit** | **Weak for the city core.** Shallow street water between buildings is mostly invisible to SAR (double-bounce), and the 2–4 day peak may fall between passes. **Workable on the eastern fringe** (Lat Krabang / Nong Chok / Min Buri paddy and open land), where water stayed longer | **Good for the surrounding plain; partial for the urban core.** Prolonged deep water. Known SAR acquisitions include 22, 24, 25 and 29 Nov 2025 (Sentinel-1A plus others) |
| Layers you can honestly show | (1) **Observed extent**: S1 change detection, eastern fringe only, with the label "urban street flooding not detectable". (2) **Reported street flooding**: a hand-curated, cited list of BMA-reported points (road name, depth in cm, date), typed `qualitative_report` with approximate geocoding | (1) **Observed extent**: S1 change detection, pre-event baseline in Oct 2025 vs. 22–25 Nov. (2) Optional reference: cite GISTDA's depth product; don't recompute depth (no own depth model) |
| Best demo role | Recognition ("last month in Bangkok") and the **routine relief planning** story (P-A support-in-place supplies; shallow, long-lasting water) | The **emergency evacuation + medical** story (deep water, boat transport, stranded people). Matches the C-01/M-01/S1 scenario best |
| Effort for you | About 0.75 day (S1 + curated report points) | About 0.5 day (S1 only) |

**Day-1 verification (12 Oct, first hour, in Earth Engine):** list `COPERNICUS/S1_GRD` IW VV/VH scenes over each AOI. Bangkok: 1–23 Sep (baseline) and 24 Sep – 5 Oct (event). Hat Yai: Oct 2025 (baseline) and 20–30 Nov 2025 (event). Record orbit and date per scene in `data/SOURCES.md`. **If Bangkok has no event-window pass over the eastern fringe**, Bangkok keeps only the reported-points layer, labeled as such. Don't fill the gap with a modeled extent.

**Scope consequence:** 0005 assumed *one fictional locality*. With two real past events, the simplest honest structure is **one locality hosting all of P-A/P-B/P-C**, plus the other event as a **second map/briefing package with no operational records**. **Decided (human, 2026-10-11): Hat Yai hosts the operational scenario; Bangkok is the second package.**
- **Hat Yai planning areas:** pick three sub-district-scale areas from the S1 extent. P-A: support-in-place, shallower/peripheral. P-B: deep, evacuation needed. P-C: no recent assessment.
- **Area IDs:** keep P-A/P-B/P-C as IDs, with real place labels only at district level. Landmarks stay generic (L1–L3, D1).
- **Bangkok areas:** IDs `BKK-1…n`, with no operational records.
- **Contract change:** `areas/{areaId}` gains `packageId` (`HY-2025-11` | `BKK-2026-09`) and `event: {name, start, end}`. Area briefings for Bangkok return operational fields as `null` with `reason: "no_operational_records_in_package"`, not zeros.

**Data honesty and sensitivity for real places:**
- Label as: "Satellite extent computed by ReachPoint from Copernicus Sentinel-1 on {dates}; households, teams, calls and quantities are synthetic."
- Attribute the data: "Contains modified Copernicus Sentinel data 2026".
- Use generic landmark names (L1–L3), not real community buildings.
- Collect no real resident data. Make no claim of operational use, and no "safe" or "dry" inference where there's no detection.
- This is an active disaster with deaths. Keep the video and deck respectful, and don't imply anyone used ReachPoint in the response.
- Cite DDPM/GISTDA figures with access dates in `docs/research/sources.md`, per AGENTS.md.

### 5.1c Hat Yai flood layer check and exposure estimate (user decision 2026-10-11)

**Feasibility evidence (research 2026-10-11).**
- A Sentinel-1 image of Hat Yai from **23 Nov 2025** exists and was already used by others. GISTDA requested Sentinel Asia emergency observation, which produced an EOS flood proxy map of Hat Yai (v0.9), AIT maps for Hat Yai District and Songkhla/Phatthalung, and an AIT ground-check product for Songkhla ([Sentinel Asia](https://sentinel-asia.org/EO/2025/article20251119TH.html)).
- GISTDA also used Sentinel-1A and RADARSAT-2 passes from 26 Oct to 29 Nov, including 24, 25 and 29 Nov ([report](https://nakmuay.charity/projects/Post_Flood_Hat_Yai_Thailand_2025-12-01/reports/flood-extent-technical)). RADARSAT-2 is not in Earth Engine.
- Sentinel-1A and 1C were both operating in Nov 2025.
- **Our own Earth Engine run is still unverified.**

**Known limits and how the map shows them.**

| Limit | Display rule |
|---|---|
| Urban double-bounce: flooded streets in the city core can look dry | Legend: "urban areas may be under-detected"; nothing is ever shaded as dry; reported flood points are drawn on top |
| 23 Nov may be before the peak | The layer is labelled "Extent on {date}", not "the flood"; use a 24–25 Nov Sentinel-1 pass if one exists |
| Our result is unchecked | Before the demo, compare it against the EOS/AIT Hat Yai maps for the same day |

**Monday flood check (about 2 h, in the user's sandbox).**
1. List `COPERNICUS/S1_GRD` scenes over Hat Yai for 1 Oct – 5 Dec 2025 (orbit, date).
2. Run change detection: October baseline vs. event.
3. Compare visually with the EOS/AIT maps and record the result in `data/SOURCES.md`.

**Fallback** if our extent is clearly wrong: use the published GISTDA/EOS/AIT polygons with attribution, after checking their licence.

**Exposure estimate per zone (Tue 13).** The estimate combines three sources:
- **Google Open Buildings v3** (covers Thailand, CC BY 4.0): buildings inside the flooded part of each zone.
- **WorldPop** 100 m population: people inside the flooded part.
- **DOPA registered population** per tambon/village ([data.go.th](https://data.go.th/en/dataset/dopa-star), yearly to 2567): a cross-check, scaled by the flooded share of buildings. Whether DOPA's statistics site also publishes registered house counts is still to be confirmed.

**Exposure display rules.**
- The output is a **range**, e.g. "About 1,400–1,900 people live in the flooded part of B-3 (estimate)". It sits next to the reviewed count, e.g. "9 reported needing evacuation".
- The label is "people living in flooded area (estimate)". It never says victims or people needing rescue.
- It never adds to reviewed counts and never creates a listing.
- It shows its source dates and its uncertainty. Buildings are not the same as households: one shophouse can hold several households, and some buildings are shops or warehouses.
- The gap between estimated and reported shows places that may have unreported needs ([unreported needs](../research/unreported-needs.md)).

Earth Engine noncommercial projects get 150 EECU-hours/month (Community tier). One small region is well within that. Register the project as noncommercial; one project only (quota farming is prohibited).

### 5.2 Real inbound phone (R2)
| Path | Status | Lead time | Notes |
|---|---|---|---|
| **Twilio + Cloud Run bridge + Gemini Live** | Documented pattern; Google's own sample apps and blog cover it | Hours once the account is paid | Twilio **trial blocks `<Stream>`**, so you need a **paid upgrade (spend decision)**. 8 kHz μ-law ↔ PCM resampling must be stateful. Cloud Run WebSockets: set a long request timeout and min-instances=1 during the demo |
| Thai local number (Twilio) | Needs identity + local-address regulatory docs | Days to weeks | **Probably won't be ready by 17 Oct.** |
| **US number (Twilio)** | Usually available right after upgrade | Minutes | A caller in Thailand pays international rates. For the demo, record one real call end-to-end. Disclose the number's country in the video |
| Google Dialogflow CX phone gateway | Google-hosted, **US numbers only**, Dialogflow agent rather than raw Gemini Live | Hours | All-Google, but Thai phone support and fit with your intake design are unverified |
| Browser mic voice | Easy | — | **Doesn't satisfy R2.** Allowed only as a dev tool or a disclosed fallback, after an explicit scope revision |

### 5.2a Using the Thai number you already have (research 2026-10-11)

What's possible depends on **what kind of number it is** (open question). If it's an ordinary AIS/True/dtac mobile SIM:

| Route | How it works | Keeps your number? | Effort / lead time | Cost & risk | Verdict |
|---|---|---|---|---|---|
| **R-a Carrier call forwarding → Twilio number** | On the SIM, dial `**21*<Twilio number>#` (unconditional forward; cancel with `##21#`). Callers dial your Thai number at domestic rates. The carrier forwards to a Twilio number; Twilio's `<Connect><Stream>` → Cloud Run → Gemini Live | **Yes** | ~1 hour once a paid Twilio number exists. **10-minute feasibility test** | You (the SIM owner) usually pay the forwarded international leg: AIS lists roughly ฿3–12/min to the US, but I found no published forwarding rate. Some prepaid plans block forwarding abroad. Twilio paid upgrade still needed (trial blocks `<Stream>`). A US Twilio number avoids Thai number paperwork | **Try first.** Ask the carrier (AIS 1175) whether international forwarding is allowed on your plan, then test |
| R-b Android phone as GSM↔SIP gateway (open-source `gsm2sip`) | SIM stays in a phone that answers calls and bridges audio to SIP → Asterisk/Twilio BYOC → Gemini Live | Yes | Needs a **rooted** Qualcomm phone (LineageOS + Magisk), device-specific audio quirks; unreviewed third-party code | Fragile; AGENTS.md bars unreviewed scripts | **Not recommended** in 7 days |
| R-c Hardware GSM gateway (GoIP/Yeastar/Dinstar class) | SIM in a box → SIP → Twilio BYOC trunk or Asterisk on Compute Engine → Gemini Live | Yes | Buy + ship + configure: 2–4 days | Purchase needed; carrier terms on automated calls through a consumer SIM unverified | Backup only, and only if R-a is blocked and you accept the spend |
| R-d New Thai virtual number (FlyNumber, Sonetel, etc.) → SIP | Reseller number routed to SIP | **No** (new number) | Document checks, "a few business days" | USD 10–18/month; NBTC-licensed partner routing | Doesn't meet "the number we already have" |
| Porting the number to a VoIP carrier | — | Yes | Weeks | — | Not feasible |

**Your case: AIS monthly (postpaid) SIM.**
- Postpaid AIS customers enable international calling by dialing `*125` or calling **1175**. AIS's own page says eligibility needs more than 4 months of registration and a good payment record. Forwarding to a non-Thai number very likely needs this enabled.
- I found **no published AIS rate or policy for forwarding to an international number**. Some carriers elsewhere forbid it entirely.
- Questions for 1175:
  1. Can unconditional call forwarding (`**21*…#`) go to a +1 (US) number on my plan?
  2. Per-minute charge for the forwarded leg?
  3. Does the forwarded call keep the original caller ID?
- The test: once a paid Twilio number exists, set forwarding, call the AIS number from another phone, check that the Twilio webhook fires, then cancel with `##21#`. About 10 minutes, a few baht.

If the number is **already a virtual/VoIP or business line** that can forward to a SIP URI or another number, R-a gets easier: point it straight at the Twilio number or a SIP domain.

**Interim plan (your instruction):** build intake on **browser voice** first, using the same Gemini Live session code over a browser WebSocket. The phone bridge reuses that code and only adds the Twilio μ-law ↔ PCM transport, so no work is wasted. Video and deck must label browser voice as browser voice. Don't call it phone intake.

Proposed gate: **Checkpoint 3 (14 Oct, end of day).** A real call from a normal phone gives two-way Thai audio, one interruption, a transcript in `reports/`, and a clean hang-up. If that fails, both of you sign a written scope revision (chat-only intake + disclosed limitation) instead of a quiet mock.

Cost order of magnitude (verify before buying): a US number is a few USD/month; per-minute voice and streaming are cents; Gemini Live audio is cents per minute. A **USD 30–50 total cap** covers the whole demo.

---

## 6. First tasks and integration checkpoints [PROPOSED]

| When (Bangkok) | You (volunteer + map) | Friend (intake + coordination + backend) | Joint checkpoint |
|---|---|---|---|
| **Sun 11 Oct (today)** | Review §3–§4 | Review §3–§4 | Approve B1–B6. Confirm registration. Create GCP project + budget alert |
| **Mon 12** | **Real extent, Hat Yai first:** register the Earth Engine noncommercial project; check which S1 scenes exist for both events (§5.1b); run the §5.1c flood check (scene list, change detection, compare with EOS/AIT maps), then Hat Yai change detection (Oct 2025 baseline vs. 22–25 Nov); export extent GeoJSON (EXT-A/B/C with acquisition dates). Draw the Hat Yai P-A/P-B/P-C boundaries over it. Bangkok package follows on Tue/Wed. Ship `contract/fixtures/areaBriefing.*.json` (synthetic operational numbers) **by noon** so your friend isn't blocked. React shell with map + list + same-ID selection | FastAPI skeleton deployed on Cloud Run; Firestore + seed script loading **your** fixtures; auth with 4 test roles; ADK Live browser-voice spike | **CP0 (evening): both deployed URLs load; the seed is shared** |
| **Tue 13** | Open Buildings counts + WorldPop exposure per area, cross-checked with DOPA registered population (§5.1c ranges) (POP-x, with reference year and uncertainty). Area briefing screen against the live `views/areaBriefing`; planning calculation `planning.py` + tests on the P-A numbers (80/20/30 → 60/30) | Chat/text intake → Gemini extraction → `proposedEvents`; desk approve/reject → case/assistance; view regeneration | **CP1: text report → coordinator approves → need on your P-B list/map (no double-count: still 24)** |
| **Wed 14** | Team list + mission screen: priority list → take family group → ack brief → set window; P-A planner submit (draft stays draft) | Publish/claim flow with capability checks; resident status page from the token; browser call screen (ADK Live) | **CP2: publish → your take + window → resident sees 13:00–14:00 for transport while medical shows "seeking team"**. Decide F2 go/no-go |
| **Thu 15** | Report resource unavailable; area briefing reacts (P-B capacity); Gemini area-explainer | Review team report → hold, withdraw window, next-update; history view | **CP3: the full emergency walk-through (§7) on the deployed app** |
| **Fri 16** | P-C field report (scoped, pending); polish map/UX; F2 if go | Reconciliation suggestion UI, retry/conflict handling, Firestore rules | **Feature freeze 18:00.** Run the joint acceptance checklist |
| **Sat 17** | Video shots (volunteer parts); deck sections: impact, map, data honesty | Video shots (phone, desk, resident); deck: architecture, AI | **Submit by 21:00 Bangkok** |
| Sun 18 | Buffer only | Buffer only | — |

Daily 15-min check-in: what changed in `contract/`, which checkpoint passed, blocker + owner.

### First connected demo: acceptance criteria (CP1 + CP2, the "walking skeleton")
1. Both screens run on deployed Google Cloud URLs, not just localhost.
2. A text report submitted through the resident intake becomes a `reports` doc with ≥1 Gemini `proposedEvent` that cites a transcript span.
3. Until the coordinator approves, nothing in `cases`/`assistance`/views changes. After approval, the P-B briefing updates in under 5 s without a reload, and the count is still 24 (C-01 already counted).
4. The coordinator approves the review, which publishes C-01's evacuation listing to the open list. Before any team takes it, the resident page says "seeking a suitable team; arrival time is not confirmed".
5. T-S takes the family group and sets a window. The resident page shows that window **for that group's transport only**, while medical stays pending/unknown. A second team tapping the same group gets "Already taken".
6. Resubmitting the same `submissionId` causes no duplicate change. A stale `expectedVersion` returns `VERSION_CONFLICT`.
7. The team-leader login can't read the transcript; the resident token can't read another case.

---

## 7. Walk-through: one synthetic emergency (all records fictional)

| # | Time | Event | Coordinator desk shows | Volunteer (T-S team screen + map) shows | Resident sees | Records that change |
|---|---|---|---|---|---|---|
| 1 | 10:10 | Resident calls (CALL-01, Thai). The Gemini Live agent asks clarifying questions: where are you now, how many people, what help | New item in the queue: "Phone report, unreviewed, possible urgent". Live transcript + labeled translation | Nothing yet. P-B still shows reviewed demand 24 | At call end, the agent says (from rules, not the model): "Your request is recorded. A coordinator will review it. Arrival time is not confirmed." Gives a status link/reference | `reports/CALL-01` created; `submissions` |
| 2 | 10:12 | Gemini extraction + reconciliation | Five proposed events (PE-01…05), each with its quote. Suggested match: C-01 (already counted in 24) | Nothing | Status page: "Received, under review" | `proposedEvents/PE-01..05` (pending) |
| 3 | 10:15 | Coordinator approves PE-01..04 and keeps PE-05 (neighbor) pending | C-01 v3: location L3 (pickup under review), 3 people, two assistance items. Medical flagged "needs qualified review", visible as suspected urgent | P-B briefing regenerates: **demand still 24** (no +3). Medical case count "1 under review". No medical narrative shown | "Evacuation: reviewed, seeking team. Medical: under review" | `cases/C-01` v3, `assistance/AS-01-EVAC`, `AS-01-MED` (review=validated), `proposedEvents` states, `history`, `views/*` |
| 4 | 10:18 | Fictional qualified reviewer records Q-01 | AS-01-MED: "Medical team capability required (FICTIONAL review)". Candidate teams by capability + availability, not by proximity | — | Unchanged | `assistance/AS-01-MED.qualifiedAssessment`, `history` |
| 5 | 10:19 | Review approval publishes C-01 evacuation (family group, RED) and medical listings | Both listed, waiting for a team; the coordinator may send T-S a direct "Can you take this?" | T-S list: C-01 pinned RED, 1.2 km, last confirmed 10:10, brief v1, pickup L3, destination D1 | **Still "seeking a suitable team; arrival time is not confirmed"** (a listing isn't a confirmation) | `listings/C-01-EVAC`, `listings/C-01-MED` (rev 1), `views/openList/*` |
| 6 | 10:20 | T-S takes the family group, acknowledges brief v1, sets window 13:00–14:00, progress "preparing" | M-01 accepted ✔ ack v1 ✔. M-M still offered | M-01 card: Accepted, Preparing, window 13:00–14:00 (team estimate) | **Transport: Rescue team T-S, expected 13:00–14:00 (team estimate, updated 10:20), preparing.** Medical: "seeking a suitable medical team; arrival not confirmed. Next update 11:00 (status update, not arrival)" | `missions/M-01` v2, `AS-01-EVAC` allocation/progress/window, `views/*`, `history` |
| 7 | 10:30 | T-S reports S1 unavailable (TEAM-01) | Red attention: "Problem reported on M-01, awaiting your review". Gemini drafts the impact list: M-01 window, P-B capacity 12 → unknown. PL-A and M-M unaffected | M-01: "Problem reported; awaiting review". The window is shown with a **timing-concern badge**, not "on time" | Unchanged until reviewed (or optionally "a timing problem was reported; we are checking") | `reports/TEAM-01` (team_report, pending), `resources/S1` = unavailable_reported |
| 8 | 10:32 | Coordinator reviews: hold M-01, withdraw window, next update 11:00, saves brief v2 | M-01 **held**, replacement unknown, owner = coordinator. Brief v2 saved, ack pending | M-01: Held; brief v2 needs acknowledgment; old window struck through. **P-B briefing: conditional capacity 12 → 0 (S1 unavailable); known gap 24**. P-A/PL-A unchanged | **Transport: on hold; new time not known; earlier 13:00–14:00 estimate withdrawn. Next update 11:00 from the coordinator desk.** Medical: unchanged (pending, no window) | `resources/S1` = unavailable; `missions/M-01` v3 held + `briefs/2`; `AS-01-EVAC.arrivalWindow=withdrawn`, `nextStatusUpdate`; `views/areaBriefing/P-B`, `views/residentStatus`, `history/H-0042` |

Negative controls to show on camera: PL-A's 30-pack draft is still a draft, P-A still shows 60 remaining / 30 unassigned, and M-M has *not* been cancelled because S1 failed.

---

## 8. Questions for both humans (grouped)

Answered by the user on 2026-10-11: 1–4, 6, 7 (see the answers table and 0009). Still open: 5 (spend cap), 8, 9–12.

**Group 1: blockers to answer today**
1. Do you authorize implementation from 12 Oct under the §6 timebox?
2. Stack: A (FastAPI + Firestore + React), B (all-Firebase TS) or C (Streamlit)?
3. ~~Phone: pay for Twilio and use a US number? Try for a Thai number? Or revise R2 now?~~ Answered: no real phone line in the prototype (R2 deferred).
4. Flood: synthetic first with F2 as a stretch? Synthetic only? Or real extent from the start (which changes the "fictional locality" scope)?

**Group 2: accounts and AI (today or tomorrow)**
5. Who owns the GCP project and billing, and what's the total spend cap? (Proposed USD 50.)
6. Gemini through Vertex AI (recommended) or an AI Studio API key?
7. Google Maps (needs a key + billing) or MapLibre/OSM?
8. Confirm you're both registered, plus the actual deadline time on the dashboard.

**Group 3: contract semantics (at the joint review)**
9. One `assistance` doc per type per case (as in §3)? Or nested inside the case?
10. Should the resident see "a timing problem was reported" *before* the coordinator reviews it (step 7), or only after review?
11. Thai for intake and English for every other screen, as the repo proposes?
12. Monorepo layout and file ownership as in §2?
