# Round 2 UI · part A

17 October 2026. Implemented steps 1–5 of the approved implementation map. All changes are under `web/`. No commit, push, deployment, package installation, backend/data change, or private ReachPoint environment-file read was performed.

## What changed

| Step | Result |
| --- | --- |
| 1 · Kit | Added spacing, radius, control-height, stage and night tokens; replaced the need colours with the approved earth ramp and made sector colours ink. Added the shared button, chip, pill, card, section-header and segmented-control kit, including aliases for existing controls. Added stroke icons. |
| 2 · Chat shell | Added the avatar/name/Gemini header, call button and overflow menu. Added grouped bubbles with replay times and response-backed read marks. Replaced the separate understood item with fact receipts under the person's message. Kept the expandable one-line family status, horizontal quick actions, round composer and judge-mode SAMPLE row. |
| 3 · Rich cards | Added location previews, sent-location and house-found cards with returned building outlines. Shortened shelter maps into expandable thumbnails, with a deepest-point marker using the returned route value. Shelter answers use the existing one-shot/retry choice sender. Added notice bands, a boat-request card, checklist progress and full-width visit answers, with a red outline for someone still inside. |
| 4 · Report and demo | Added the wide-screen 340px / fluid / 470px layout, central phone stage and numbered headings. Combined depth bars and the water toggle into the map card. Added turn-grouped evidence with folded older turns, newest-content scrolling and receipt/timeline highlighting. Moved family simulation and all clock actions into a dark DemoBar. Report controls wait for `status.zoneId`, show completed events and suggest the next event. Shared headers use the clock-only bar on other pages. |
| 5 · Water | Preserved the data grid while rendering fixed band alpha at 38/46/54/62%, with a 4× smoothed canvas and 1.5px blur. Shared zoom opacity is 1 / 0.6 / 0.35, with listener cleanup. Report maps cap at zoom 18 and focus at 16; shelter maps use the same canvas renderer. House outlines stay above water with an ink halo. |

Thai comes first in the new labels, with English glosses retained. New controls use 44px tap targets. Responsive columns, bounded scroll rows, wrapping message content and removal of the device border on narrow screens support the 390px layout. Mobile tabs, AI toast and the demo bottom sheet belong to step 7 and are not part of this change.

Existing send/replyTo callbacks, simulation application, status/inbox polling, voice-call handlers, GPS/pin flow, shelter directions, replay actions and evidence content remain connected. Reported request, team plan and confirmed pickup remain separate; unknown values are not replaced with illustrative numbers.

## Files changed

Paths below are relative to `web/`.

- Shared tokens/icons: `src/ui/tokens.css`, `src/ui/Icon.tsx`.
- Styles: `src/features/v2/ui/kit.css` (new), `src/features/v2/ui/phase-one.css`, `src/features/v2/ui/phase-three.css`, `src/features/v2/ui/phase-four.css`, `src/features/v2/v2.css`, `src/features/v2/volunteer/volunteer.css`.
- Chat/cards: `src/features/v2/Phone.tsx`, `src/features/v2/ui/ChatShell.tsx` (new), `src/features/v2/ui/FamilyFollowUp.tsx`, `src/features/v2/ui/LocationCard.tsx`, `src/features/v2/ui/ShelterCard.tsx`, `src/features/v2/ui/NoticeCard.tsx` (new).
- Report/evidence/demo: `src/features/v2/V2Page.tsx`, `src/features/v2/ui/Shared.tsx`, `src/features/v2/ui/DemoBar.tsx` (new), `src/features/v2/ui/DepthBars.tsx` (new), `src/features/v2/ui/TraceTimeline.tsx` (new), `src/features/v2/ui/reportTrace.ts`, `src/features/v2/ui/trace.ts`.
- Water: `src/features/v2/BoardMap.tsx`, `src/features/v2/floodLayer.ts`.
- Tests: new `src/features/v2/floodLayer.test.ts`, `src/features/v2/ui/ChatShell.test.tsx`, `src/features/v2/ui/NoticeCard.test.tsx`, `src/features/v2/ui/DemoBar.test.tsx`; updated `src/features/v2/ui/ShelterCard.test.tsx`.
- Handoff: `ROUND2-PART-A.md` (this file).

## Verification

After every step, ran the requested sequence from `web/`, fixing failures before proceeding:

```sh
npx tsc -b && npm run check:tokens && npm test && VITE_DATA=api npm run build
```

| Checkpoint | TypeScript | Tokens | Tests | API-mode production build |
| --- | --- | --- | --- | --- |
| Step 1 | Pass | Pass | 152 / 152, 26 files | Pass |
| Step 2 | Pass | Pass | 154 / 154, 27 files | Pass |
| Step 3 | Pass | Pass | 159 / 159, 28 files | Pass |
| Step 4 | Pass | Pass | 165 / 165, 29 files | Pass |
| Step 5 and final review | Pass | Pass | 167 / 167, 30 files | Pass |

Final output: `Tokens check passed: no raw colours outside tokens.css`; `Test Files 30 passed (30)`; `Tests 167 passed (167)`; production build completed successfully.

Tests cover receipt reader labels and pending/read states, existing status formatting and choice-send locking/retries, unknown status fields, notice bands, visit-answer disabling, initial checklist progress, demo-bar enablement/busy states, trace folding, actual depth/range values, water alpha/upsampling and zoom-listener cleanup. The existing broader test suite also passes.

`git diff --check` passed. The source-scope check found only `web/` changes, with no staged changes. A credential-pattern scan of changed files found no matches. Build output still includes Vite's large-chunk advisory; server-rendered router tests emit the existing React `useLayoutEffect` warnings.

## Left undone / verification limits

- Optional water iso-lines were not implemented.
- Steps 6–8 are outside this part A request.
- The API is unavailable from this sandbox. Live API, Google Maps rendering, GPS permissions, microphone/voice and browser screenshot/390px measurements were not exercised. Type checks and tests verify the frontend contracts and covered behavior; they do not establish live integration or pixel-level visual verification.
