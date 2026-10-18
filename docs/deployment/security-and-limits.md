# Judging security and limits

All longer caps reset every **15 minutes**. They exist only against spam and runaway cost; a judge clicking through the demo several times never meets them. The Gemini counter is kept in memory (a restart opens a fresh window), so no model call waits on Firestore.

Prepared 18 October 2026 for 19 October–6 November. These are demo safeguards for **one Python worker on one Cloud Run instance**, 1 vCPU / 1 GiB, behind Firebase Hosting. They are not authentication or a DDoS service. All households remain synthetic. No deployment, billing change, key change or uptime check was performed by this task.

## Request limits

Minute limits are thread-safe token buckets: the full allowance is available initially and replenishes continuously. IP limits span rooms; additional IP/room buckets keep the demo-room identity in the key. The session bucket spans IPs within its room. Changing rooms never bypasses the IP allowance. Idle buckets are removed on traffic at least every 60 seconds. Daily allowances reset at UTC midnight, independently of the replay clock.

| Action | Limit |
|---|---|
| Chat turns (typed and Live tool turns) | 30/min/IP and 20/min/session/room |
| Session creation | 20/min/IP |
| New in-memory demo room or room reset | 10/min/IP |
| Copilot questions | 8/min/IP and 30 per 15 minutes/IP |
| Live calls | 3 concurrent globally; 1 concurrent/IP; 4 starts per 15 minutes/IP |
| Live duration | Hard stop at 5 minutes, including connection setup |
| Other POSTs, including classic when locally enabled | 120/min/IP |
| GETs, including polling, health, assets and classic | 600/min/IP |
| HTTP POST body | 32 KiB, including unknown JSON fields |
| Live WebSocket frame | 64,000 bytes audio; 4,096 characters JSON; spoken turn 600 characters |
| In-memory rooms | 300, adjustable with `REACHPOINT_MAX_ROOMS` |
| Sessions in a v2 room | 200; reset that room to clear them |
| Derived board cache | 8 rooms globally, at most 2 snapshots each |
| Gemini output default | 2,048 tokens per REST model call |

HTTP limits return 429, `{"error":"rate_limited","retryAfter":N}` and `Retry-After: N` (whole seconds). A full room's session allowance returns 60 seconds; it needs a reset rather than replenishment. A busy room store returns a 5-second retry. Live admission occurs after accepting the socket so the browser can receive a bilingual error with the same fields, then close 1013; invalid/missing Origin is rejected before acceptance (1008). Voice-turn limits send a bilingual wait message without recording a turn. Normal demonstrations, repeated 2–3 times in 20 minutes, fit these limits; judges sharing one public IP share its allowance.

The browser's shared API client reads 429 before generic errors, and the chat displays “Too many messages at once — wait N seconds / ส่งข้อความถี่เกินไป กรุณารอ N วินาที”. It does not automatically retry writes. The server returns `X-Demo-Room` so a caller can retain a fresh room if an invalid ID was supplied. Browser-generated room IDs are validated too.

## Paid Gemini budget

| Variable | Default | Effect |
|---|---|---|
| `RP_GEMINI_CALLS_15MIN` | `400` | All Gemini REST attempts (including retries and copilot tool rounds) plus each Live connection reserve a call before contacting Google |
| `RP_LIVE_MIN_15MIN` | `45` | Live starts reserve five minutes; successful cleanup refunds unused minutes |
| `RP_FIRESTORE` | unset | `1` saves demo rooms in Firestore; usage counters are always in memory |
| `RP_CLASSIC_ENABLED` | `0` on Cloud Run, `1` locally | Cloud Run rejects classic POSTs with 410; classic voice is always retired |
| `REACHPOINT_GEMINI` | `auto` | Judging deploy script uses `key`; keep the paid key in Secret Manager/environment |
| `REACHPOINT_AI` | `on` | `off` avoids live Gemini work (tests/offline) |

`/api/v2/health` exposes `gemini: {calls, cap, capped, liveMinutes, liveCap, resetsInS}`. A reached cap makes the reader and copilot use their existing **rules** label. Live reports unavailable and typing still works. Failed model attempts count because they may have reached Google. A process crash may retain the full five-minute reservation; this deliberately overcounts. The counter uses one writer under a lock, matching the one-instance/one-worker deployment. Do not add workers, overlap serving revisions, or scale replicas without transactional distributed quotas.

All limits, including the Gemini budget, are in memory and restart with the instance. A call-count cap is not a dollar cap: token use, Live audio, geocoding, Maps, Firestore and always-on Cloud Run have separate costs. Budget alerts notify; they do not stop spending. Check counters and Cloud Run memory daily during judging.

## Memory and persistence

Rooms are evicted in least-recently-used order; requests and calls pin their active room until cleanup. Pending Firestore timers are cancelled and the latest snapshot is saved synchronously before eviction. A failed flush keeps the room and returns a retry instead of discarding it. Firestore restores a saved room on its next visit. Memory-only rooms are lost on eviction. The existing 900,000-byte Firestore snapshot guard can trim the oldest live messages; oversized sessions can still make a save fail. A failed save must be investigated through `lastSaveError` before resetting anything.

The room and cache ceilings reduce accumulation; this task does not prove a worst-case 1 GiB bound or three-week availability under arbitrary traffic. There is no paid load test. Shared global allowances preserve a useful typed rules demo if model capacity is exhausted.

## Browser boundaries

Both FastAPI and `firebase.json` set:

- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-Frame-Options: DENY`
- `Permissions-Policy: microphone=(self), geolocation=(self)`
- `Content-Security-Policy`: self by default, no objects, no framing, self forms/base; scripts from self and Maps; styles from self, inline styles and Google Fonts; fonts from `fonts.gstatic.com`; images from self/data/blob, Google APIs, gstatic, google.com and googleusercontent.com; connections to self/Google Maps services and the two Cloud Run WebSocket origins; self/blob workers and media. Exact policy lives in `api/security.py` and is mirrored without changes in Firebase headers.

No inline scripts are allowed. Maps needs `unsafe-eval` and blob scripts per its published CSP guide. Maps frames may load Google origins; embedding ReachPoint itself remains denied. Inline styles are needed by Maps, positioned pins and the flood canvas. External URLs were inventoried in `web/src`, and the built `web/dist/index.html` uses only local module assets and Google Fonts. Google Maps directions links are navigations, not embedded frames. Existing `Cache-Control` behavior is retained: Firebase's edge rule is still `no-store`; `/api/v2/sim.bin` still explicitly has `public, max-age=86400` at the API.

Browser HTTP requests with an Origin must match this exact allowlist, also used by v2 WebSockets:

- `https://reachpoint-main.web.app`
- `https://reachpoint-main.firebaseapp.com`
- `https://reachpoint-900867850704.asia-southeast1.run.app`
- `https://reachpoint-plxxmixu6a-as.a.run.app`
- `http://localhost` and `http://127.0.0.1` at ports 3000, 4173, 5173, 8000 and 8080

Requests without Origin remain available for health checks and CLI clients; CORS is not caller authentication. WebSockets require Origin. Invalid room IDs become fresh random rooms at the HTTP boundary; accepted pattern is `^[A-Za-z0-9_-]{1,64}$`. Household and zone path/query IDs are checked before lookups. POST strings and lists are bounded, including classic models (general text 2,000, string-list items 80, lists 200, count dictionaries 40). V2 keeps tighter text limits: chat/copilot 600, plans 300, team names 80, checklist 20.

The requested identity policy uses the **left-most valid X-Forwarded-For IP**, falling back to `request.client.host` if the first entry is missing/invalid. It ignores `Fastly-Client-IP`. Google documents a proxy chain and warns that existing XFF entries can be supplied by clients. The left-most entry cannot be treated as authenticated identity on the directly public Run origins. Firebase's published documentation does not establish a trusted Fastly header contract. Verify actual Hosting and direct-origin forwarding before judging; global paid caps remain necessary even when IP identities can be spoofed.

## Prompts and classic routes

The v2 intake reader and copilot already delimit caller text as data. The plan reader now wraps the plan in labelled JSON data (including the local Claude route). Classic intake extraction already uses a data block; classic conversation SDK inputs now explicitly label JSON as caller data. Typed Live input is labelled JSON data; the Live system instruction treats speech as data and delegates recorded turns to the deterministic intake agent. These boundaries and quoted-fact checks reduce injection effects; they are not a proof that a generative model cannot follow malicious speech.

On Cloud Run, **all classic POST routes outside `/api/v2/`** return 410: intake, call sessions/turn/location/pin/confirm, location preview, claims, allocations, team/resource/listing changes, report approvals/rejections/links, zone missions/segments, demo reset/replay, water observations and plan asks. V2 uses none of these writes. `/api/config` remains for the Maps browser key; classic GET views remain available under GET quotas and headers, but classic briefing GETs cannot schedule model work while disabled. `/api/call/sessions/{id}/live` is disabled everywhere. The deploy script explicitly sets `RP_CLASSIC_ENABLED=0`.

Credentials are read from environment only; implicit private-file fallback was removed from Gemini and Pinpoint. No private credential file was read. The urgent landmark reply now asks to confirm/move the pin in English and Thai, without repeating “Where is your house?”.

## Owner commands (prepared, not executed)

The read-only billing lookup failed in this sandbox because gcloud could not access its credential database. Run these in your authenticated terminal. The budget covers the judging interval (exclusive end 7 November), $50 on the linked billing account, filtered to this project. Confirm who receives the default billing-account alert emails.

```sh
RP_BILLING_ACCOUNT=$(gcloud billing projects describe reachpoint-main --format='value(billingAccountName)')
RP_BILLING_ACCOUNT=${RP_BILLING_ACCOUNT#billingAccounts/}
gcloud billing budgets create \
  --billing-account="$RP_BILLING_ACCOUNT" \
  --display-name='ReachPoint judging 19 Oct–6 Nov' \
  --budget-amount=50USD \
  --filter-projects=projects/reachpoint-main \
  --start-date=2026-10-19 --end-date=2026-11-07 \
  --threshold-rule=percent=0.5,basis=current-spend \
  --threshold-rule=percent=0.9,basis=current-spend \
  --threshold-rule=percent=1.0,basis=current-spend
```

Identify the **Gemini server key ID**, not its secret value. Do not apply this restriction to the separate Maps browser key. Inspect existing restrictions first; `--api-target` replaces the API target list unless `--append` is used. Keep only Generative Language API for this key.

```sh
gcloud services api-keys list --project=reachpoint-main --location=global --format='table(name,displayName)'
# Replace GEMINI_KEY_ID with the Gemini server key's resource ID.
gcloud services api-keys update GEMINI_KEY_ID \
  --project=reachpoint-main --location=global \
  --api-target=service=generativelanguage.googleapis.com
```

Create an HTTPS uptime check through Hosting, matching `ok: true`; then attach a notification/alert policy in Monitoring so failures notify the owner (a check alone does not notify).

```sh
gcloud monitoring uptime create 'ReachPoint judging health' \
  --project=reachpoint-main --resource-type=uptime-url \
  --resource-labels=host=reachpoint-main.web.app,project_id=reachpoint-main \
  --protocol=https --port=443 --path=/api/v2/health \
  --request-method=get --period=5 --timeout=10 --validate-ssl=true \
  --status-codes=200 --matcher-type=contains-string --matcher-content='"ok":true'
```

After the reviewed image is deployed, set service-wide minimum/maximum to one, clear the current revision minimum, and preserve existing secrets. Confirm no tagged old revision is kept warm:

```sh
gcloud run services update reachpoint --project=reachpoint-main --region=asia-southeast1 \
  --min=1 --max=1 --min-instances=0 --max-instances=1 --cpu=1 --memory=1Gi --no-cpu-throttling \
  --update-env-vars=RP_FIRESTORE=1,RP_GEMINI_CALLS_15MIN=400,RP_LIVE_MIN_15MIN=45,RP_CLASSIC_ENABLED=0
```

## Verification after deployment

Validation on 18 October: **380 API tests passed** (including 36 new hardening cases); **234 web tests passed** across 42 files. TypeScript, design-token checks, production build, shell syntax, whitespace, JSON and changed-file sensitive-pattern checks passed. The build retains its existing large-chunk warning. Browser automation reported no available browsers, so the browser CSP smoke check could not run.

Local automated checks cover limit/refill/day rollover, parallel access, persistence/failure, Live slots and timeout cleanup, room flush/eviction, session caps, CORS/Origin, body/ID bounds, 429 messages and header mirroring. Paid Gemini/Firestore and the deployed edge were not exercised.

If a headless CSP check is unavailable, perform this exact browser check from **both Hosting origins and both Run origins**:

1. Open `/v` and the resident demo in English and Thai with DevTools Preserve log enabled. Verify document, API success/error and OPTIONS responses have the expected headers. Confirm no CSP violations.
2. Load Google Maps, zoom to satellite tiles, move a roof pin, request GPS, and show neighbour outlines and the flood canvas. Confirm Fonts and Maps/tiles load without blocked network requests; test the external directions link.
3. Permit microphone; start/end a Live call, type during the call, and leave a call running past five minutes. Confirm the WebSocket uses an allowed Run URL, closes cleanly, frees the slot, and typed chat still works. Repeat two calls from different devices/IPs; the fourth simultaneous call must wait.
4. Repeat every normal demo step 2–3 times in 20 minutes. Exercise a 429 in a disposable room and confirm its bilingual wait message, then recovery after `Retry-After`.
5. Reset only that room; revisit an evicted saved room. Restart the instance and confirm `callsToday` persists. With a temporarily low cap in a test revision, confirm reader/copilot show `rules` and voice leaves typing available.
6. Verify no unexpected public Run revision receives traffic. Watch peak instance memory and latency; the 300-room cap alone is not a memory benchmark.

## Sources

Accessed 18 October 2026. Google docs support command/header behavior, not verification of this deployment.

- [Maps CSP guide](https://developers.google.com/maps/documentation/javascript/content-security-policy) — Maps eval/blob, image, connection and frame requirements.
- [Google request headers](https://docs.cloud.google.com/functions/docs/reference/headers) — XFF chain convention; specifically Cloud Run functions, not a Firebase header guarantee.
- [Load balancer XFF handling](https://docs.cloud.google.com/load-balancing/docs/https#x-forwarded-for_header) — existing header entries are not verified by the load balancer.
- [Hosting cache behavior](https://firebase.google.com/docs/hosting/manage-cache) — dynamic cache configuration; no trusted Fastly identity contract established.
- [Budget create CLI](https://docs.cloud.google.com/sdk/gcloud/reference/billing/budgets/create) — amount, project filter, dates and threshold flags; alerts only.
- [API-key update CLI](https://docs.cloud.google.com/sdk/gcloud/reference/services/api-keys/update) — API service target restriction.
- [Uptime create CLI](https://docs.cloud.google.com/sdk/gcloud/reference/monitoring/uptime/create) — HTTPS URL checks and content matching.

- [Cloud Run update CLI](https://docs.cloud.google.com/sdk/gcloud/reference/run/services/update) — service-wide `--min`/`--max` versus per-revision instance settings.
