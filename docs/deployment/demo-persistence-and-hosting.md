# Demo persistence and Firebase Hosting

Implemented at the owner's request on 17 October 2026. Only synthetic v2 demo rooms are persisted. No cloud
resources were created by this change. Classic rooms and call sessions were removed on 18 October 2026 ([decision 0012](../decisions/0012-v2-only-repository.md)).

## Owner setup

Run these after authenticating gcloud, with permission to enable services, create the database and grant IAM:

```sh
gcloud services enable firestore.googleapis.com firebasehosting.googleapis.com --project reachpoint-main
gcloud firestore databases create --database='(default)' --location=asia-southeast1 --type=firestore-native --project=reachpoint-main
gcloud projects add-iam-policy-binding reachpoint-main --member='serviceAccount:900867850704-compute@developer.gserviceaccount.com' --role=roles/datastore.user --condition=None
PROJECT=reachpoint-main scripts/deploy.sh
npx -y firebase-tools@13 login
PROJECT=reachpoint-main scripts/firebase-deploy.sh
```

Create the database only if `(default)` does not already exist. The commands follow Google's
[database management guide](https://docs.cloud.google.com/firestore/native/docs/manage-databases) and
[Firestore IAM guide](https://docs.cloud.google.com/firestore/native/docs/security/iam).
The service account is the default Compute Engine identity: `scripts/deploy.sh` derives it from the project
number and now passes it explicitly to Cloud Run. No downloaded keys are used.

The Firebase project and Hosting site must already be available for `reachpoint-main`. This change does not
register an existing GCP project with Firebase. Add both Hosting domains to the Maps browser key's allowed
HTTP referrers if needed: `https://reachpoint-main.web.app/*` and `https://reachpoint-main.firebaseapp.com/*`.

## Stored data and failure behavior

`RP_FIRESTORE=1` enables the `v2rooms` collection in `(default)`, using ADC and the environment project. The
health endpoint `/api/v2/health` reports `store` and `lastSaveError` (exception type only). In local development
and tests the default is memory. Save errors are logged at most once a minute and do not fail requests.

A daemon timer debounces changes for 1.5 seconds. A sudden process stop can lose changes still waiting for the
timer or an in-flight write. Failed writes are retried on the next mutation. First access loads the saved room;
a failed load falls back to memory. Keep one active Cloud Run instance, as deployed by the script: this is
restart persistence, not coordination between multiple writers.

The document holds the replay clock, sequence, live messages, posted plans, alerts, pulled scenario times,
family sessions and do-first marks. Seed messages stay in the scenario files and are replayed on restoration.
Runtime locks, board caches and derived message effects are rebuilt. Complex fields are JSON strings to
preserve nested arrays and parsed `Read` facts. Size includes UTF-8 bytes and an overhead allowance; the oldest
live messages are removed from the saved copy to stay below 900,000 bytes, with a warning. If sessions or plans
alone exceed the limit, the save fails visibly through health instead of writing an oversized document.
Reset cancels pending writes and deletes the saved document in the background, ordered after in-flight saves.

## Hosting and voice

The empty `web/firebase-public` directory lets every path, including `/`, reach the Cloud Run service
`reachpoint` in `asia-southeast1`. `Cache-Control: no-store` prevents stale HTML and room responses. The frontend
uses relative `/api` calls. Both voice clients bypass Hosting on `.web.app` and `.firebaseapp.com`, using
`VITE_WS_ORIGIN` or `https://reachpoint-900867850704.asia-southeast1.run.app`. Set the build variable before the
web build if the Cloud Run origin changes. Both socket URLs carry `room`; neither backend socket handler
rejects the Hosting origin. See Google's [Cloud Run rewrite guide](https://firebase.google.com/docs/hosting/cloud-run)
and [WebSockets guide](https://docs.cloud.google.com/run/docs/triggering/websockets).

Hosting has a 60-second HTTP timeout. The external work on these routes previously could exceed it:

- `POST /api/v2/v/copilot`: up to two models with several 20-second tool rounds; now a 35-second total model budget,
  followed by the deterministic fallback.
- `POST /api/v2/chat/sessions/{sid}/turn`: model reading and geocoding with retries; now a 15-second reader budget,
  parallel geocoding with a 10-second budget per lookup (at most one additional lookup).
- `POST /api/v2/plans`: model retries; now a 20-second total budget with the rule parser as fallback.

These are budgets for optional external reads, not an end-to-end latency guarantee under saturation or a cold
CPU-heavy rebuild. Late model results cannot mutate rooms. WebSocket calls retain their separate 10-minute cap
and Cloud Run's 900-second request timeout. No non-WebSocket route intentionally streams or waits over 60 seconds.
The legacy call conversation can still be lost on a Cloud Run restart; the persisted family experience is v2.

Sources accessed 17 October 2026; cloud IAM, Firebase registration, billing and live deployment were not verified.
