# Round 2, Part F — Volunteer mission

Implemented the accepted-zone handoff and `/v/mission/:zoneId` within `web/`.

## Files changed

- `src/App.tsx`: mission route beside the volunteer routes.
- `src/features/v2/api.ts`: optional zone `shelterOptions` response typing; no backend change.
- `src/features/v2/volunteer/OverviewPage.tsx`: after a successful plan post, remember the trimmed team name, save the mission, navigate, and retain a direct mission link in the posted message if navigation fails.
- `src/features/v2/volunteer/shared.tsx`: saved-mission volunteer navigation link.
- `src/features/v2/volunteer/mission.ts`: validated storage with blocked-storage fallback, visiting order, completed-state detection, and directions URLs.
- `src/features/v2/volunteer/MissionPage.tsx`: live zone data, mission details/progress, numbered household cards, translated needs/depth/access context, directions, and confirmed outcome actions using the existing team-name opener.
- `src/features/v2/volunteer/MissionMap.tsx`: hybrid map, Map/Satellite controls, polygon/house fitting, numbered selectable markers, dashed visiting order, and the existing corrected flood canvas/zoom binding under a 0.5-opacity layer. Projection access is guarded.
- `src/features/v2/volunteer/volunteer.css`: sticky 60/40 desktop layout, 45vh map above the phone list, wrapping actions, 44px targets, and mission text at least 14px. All colours reference existing tokens.
- `src/features/v2/volunteer/mission.test.ts`: storage round trips, malformed records, denied/quota storage, ordering, completed states, and directions URLs.
- `src/features/v2/volunteer/MissionPage.test.tsx`: page rendering from sample zone data in Thai and English, numbered cards, different-zone mission details, and the all-done state.
- `src/features/v2/volunteer/MissionPage.interactions.test.tsx`: team-name requirement, confirmation, cancellation, all three outcomes, nearest optional shelter, failure/retry, and refresh after success.
- `src/features/v2/volunteer/ZonePanel.mission.test.tsx`: successful handoff, navigation-failure fallback, and failed-post behavior.
- `ROUND2-PART-F.md`: this record.

## Verification output

Run from `web/`:

```text
npx tsc -b
(exit 0)

npm run check:tokens
Tokens check passed: no raw colours outside tokens.css

NODE_OPTIONS=--experimental-global-webcrypto npm test
Test Files  39 passed (39)
Tests       220 passed (220)

VITE_DATA=api npm run build
✓ 176 modules transformed.
✓ built
```

The initial unmodified `npm test` invocation failed 7 existing tests in 5 files because test workers lacked the global `crypto` API (`apiMode`, `location`, `Flood`, `ResourceFailure`, `ReviewQueue`). Enabling Node's Web Crypto flag makes the full suite pass without changing unrelated application/test configuration. Existing React Router SSR `useLayoutEffect` warnings remain. The production build emits a bundle-size warning for its main chunk exceeding 500 kB.

`git diff --check` passes. New files were also checked for trailing whitespace, conflict markers, and credential-shaped content. Changes are confined to `web/`.

## Limits

- Browser layout and live Google Maps/API behavior are not runtime-verified: the sandbox refused the local Vite listener (`listen EPERM`) and a headless Chrome launch. The 390px layout is implemented in CSS; no claim of measured no-overflow is made here.
- Shelter outcomes use the nearest entry by `km` only when zone `shelterOptions` are supplied; otherwise `shelterId` is omitted. A visiting line is explicitly labelled as an order, not a road route.
- Creating `codex/volunteer-mission` was blocked by read-only Git refs. Edits remain uncommitted on the existing branch. Nothing was committed, pushed, or deployed; no backend/data files were changed and the private env file was not read.
