# V2 cleanup retest — 18 October 2026

Target: uncommitted `codex/v2-repo-cleanup`, based on `claude/v2` revision `e3432e5`.
Scope: [decision 0012](../decisions/0012-v2-only-repository.md).

## Automated checks

- Backend and retained data tests: **212 passed** on a fresh run.
- Frontend: **139 tests passed in 26 files**; TypeScript and design-token checks passed.
- Production frontend build passed: main JavaScript 370.42 kB, CSS 103.38 kB, no oversized-chunk warning.
- Existing Starlette/httpx deprecation warning remains; no dependency upgrade was attempted.
- Tests used the existing project interpreter and cached pytest helpers without installing packages.

## Running application checks

Started the built app locally on its documented port, with rules-only reading, browser voice off,
Firestore off and external API keys disabled. Used only synthetic reports and teams.

- Real HTTP: overview, Report, Volunteer, zone/case/mission deep links and retired browser URLs
  serve the built SPA; JavaScript/CSS assets load.
- Health, geo, timeline, state, volunteer overview, simulation binary and terrain endpoints return 200.
- Retired intake, call-session and demo-reset POSTs return 404.
- Browser: submit the sample family report, inspect quoted facts, location and depth; request a team.
- Browser: see the same household in B5, set a synthetic boat team with six seats, generate a labelled
  rules visiting-order suggestion, post it and open the mission route.
- Browser: mission has the household, route/run details and pickup action. Confirming the team outcome
  sends a pickup notice. Separately verified real HTTP plan notification and pickup notification.
- With the family phone kept open, the pickup notice arrives; the family confirms they are out and safe.
  The case retains the confirmation in its history and is evacuated.
- Browser error/warning log was empty when checked during the volunteer planning flow.

## Limits found and limits of this run

The family phone creates a new chat when its page mounts. Switching from Report to Volunteer in the
same tab and returning therefore starts over. This behavior is present in the pre-cleanup Phone source;
it is not introduced by retiring classic. Keep the family phone in its original tab and use another
for Volunteer. The root README's demonstration steps now say this explicitly.

Some confirmation choices send Thai text even in English mode, and the reply can then be in Thai.
This existing language behavior was observed, not changed in this cleanup.

Live Gemini extraction/suggestions/voice, Google Maps rendering, Pinpoint and real Firestore access
were not exercised. Their fallback or stubbed paths passed; this does not verify credentials, billing,
current deployed configuration or external availability. No clean container rebuild or deployment was
performed. The temporary local server and test tabs were closed after checking.
