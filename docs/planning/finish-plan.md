# Finish plan (13–17 Oct 2026)

Date: 13 Oct 2026. This replaces the open items in [build-week tasks](build-week-tasks.md) wherever they disagree.

## Where we stand

Two independent mock judges scored the prototype on the official rubric. Both put it just below the finalist level:

| Criterion | Weight | Claude judge | Codex judge |
|---|---:|---:|---:|
| Technical Merit & Gen AI | 40% | 6.0 | 6.0 |
| Problem & Impact | 25% | 7.0 | 6.5 |
| Innovation | 25% | 6.5 | 6.5 |
| UX | 10% | 7.0 | 7.0 |
| **Total** | | **64.75** | **63.5** |

Full reports: [Claude judge](../reviews/judge-2026-10-13.md), [Codex judge](../reviews/codex-judge-2026-10-13.md).

**Both agree:**
- The core loop, the cited facts, the solver and the bilingual phone design are real strengths.
- We miss three hard requirements: a live link, the video and the PDF deck.
- The current deploy would crash.
- Docs claim things that aren't built.
- The AI is not measured.

**Bugs Codex found (confirmed):**
- The extractor checks that a quote *exists*, not that it *supports* the fact. "Nobody is unconscious" is accepted as the danger sign "unconscious", and "50 adults" is accepted with the quote "There are 2 adults". See `api/intake/extract.py`, `validate`.
- The briefing checker accepts a number if it appears anywhere, not under the right label (`api/ai/briefing_text.py`).
- Approve and reset have no protection. The review queue sends exact coordinates.
- Triage and briefings run after the reply is sent, so Cloud Run needs `--no-cpu-throttling`.

**Target:** 78–82, by proving three things instead of adding features: **it runs live, the AI is reliable (with numbers), and one story people remember.**

## 1. Run live (Tue–Wed) — owner: Claude, deploy approved by the user

| Task | Done when |
|---|---|
| Move `ortools` into `api/requirements.txt`. In the Dockerfile, copy `data/hy-2025-11/*.geojson`, `data/surge.py` and `data/packages.py` | The container starts and `/api/health` answers |
| Gemini key in Secret Manager (`gemini-api-key`); `--set-secrets` in `scripts/deploy.sh` | The live intake shows `source: gemini` |
| `--no-cpu-throttling --min-instances 1 --max-instances 1` | Triage and briefings finish on Cloud Run |
| Add the Cloud Run URL to the Maps key's allowed sites | The Google map loads live |
| Demo coordinator code on approve, reset and desk writes; family and team pages stay open | Approving without the code returns 403 |
| `reviewQueue` hides exact coordinates unless the code is sent | The family page never receives a point |
| Full flow on a phone on the live URL | Filmed once end to end |

## 2. Trustworthy AI (Wed) — owner: Claude

- **Negation:** a danger quote with no / not / nobody / ไม่ / ไม่มี / ไม่ได้ drops the sign and marks it "check with caller". The keyword stand-in gets the same check, and the prompt says negated, past or hypothetical dangers are not danger signs.
- **Counts:** if the people quote has numbers, the counts must match them. Otherwise the field is dropped and flagged.
- **Briefing numbers:** each number is checked against its own label.
- **Tests:** Codex's probes become regression tests.

## 3. Measured AI (Wed–Thu) — owner: Codex, reviewed by Claude

- **Test set:** `contract/evals/intake.jsonl`, 36 labelled synthetic Thai/English messages: corrections, negations, two households at one landmark, real duplicates, a new danger added to an existing case, unknown counts.
- **Runner:** `api/scripts/eval.py` runs Gemini 3 times against the keyword stand-in.
- **Measures:**
  - accuracy per fact;
  - missed danger signs and false alarms;
  - duplicate links found and wrong;
  - correct "unknown" answers;
  - latency (median and 95th percentile);
  - how often it fell back to the stand-in.
- **Output:** `docs/eval/results.md`, committed with the failures shown. One chart goes into the deck and the video.

## 4. Visible AI (Thu) — owner: Claude

- The desk shows the triage agent's real tool calls from the ADK events (`api/ai/triage.py`).
- For same-landmark or correction cases, the agent proposes a question to ask the caller. The coordinator decides.
- The label changes to "Danger first, then oldest · agent checks for duplicates" (not "sorted by the triage agent").

## 5. The memorable story (Thu)

**Pitch:** *"The map is quiet. The family isn't safe."*

1. B-4 has no calls but is marked unchecked.
2. A team checks it and finds an elderly couple who never called.
3. The coordinator approves, and the request becomes a rescue job.
4. Then the boat breaks down, and the family's arrival time is withdrawn honestly.

**Hidden from the demo path:** wading advice, flood-depth guesses, Bangkok and the planner scenes, and the 1,200-message replay presented as AI (it uses rules).

## 6. Story and evidence for judges (Thu–Fri)

- **README for judges:**
  - the live link;
  - a 60-second "try this" path;
  - an architecture diagram of what actually runs;
  - the AI test results;
  - limits.

  Voice, Vertex, Firestore and sign-in are marked **planned**.
- **"How we differ" table** against the 1784 hotline, LINE groups and thaifloodhelp.
- **One real reaction (friend, if possible):** show the app to a Hat Yai rescue volunteer or coordinator and quote them with permission. This is the only thing that raises the impact score.
- **Finish the missing Thai strings** and do a final pass at 390 px.

## 7. Video and deck (Fri)

**Video, 2:50, English with Thai on screen:**

| Time | Content |
|---|---|
| 0:00–0:15 | Hook |
| 0:15–0:45 | A Thai message becomes Gemini facts with quotes |
| 0:45–1:10 | The agent's duplicate check and a clarifying question |
| 1:10–1:30 | The boat breaks down |
| 1:30–2:05 | B-4 quiet zone |
| 2:05–2:25 | AI test numbers and architecture |
| 2:25–2:50 | Adoption plan and links |

**Deck, 10 slides (PDF):**
1. Promise
2. Problem
3. Users
4. Workflow
5. How we differ
6. Gen AI design
7. AI test results
8. Architecture
9. Impact and cost
10. Links and next step

**Saturday** is buffer: rehearse on a phone, re-run the tests, check the live link and submit before the deadline.

## Not doing this week

Voice (Gemini Live), photo input, Firestore and real sign-in. Each is risky to build by Saturday, and judges gain more from proof than from more features.

## Who does what

| Who | Tasks |
|---|---|
| Claude | 1, 2, 4, README |
| Codex | 3 (AI test), then UI polish from 6 |
| **Friend** | **Pinpoint `_request` ([handoff](pinpoint-handoff.md)); contact a Hat Yai volunteer for one reaction; review PRs; keep secrets out of Git** |
| User | Approve deploys and pushes, record the video voice-over, final submit |
