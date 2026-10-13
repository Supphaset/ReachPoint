# Pinpoint handoff (for the friend)

Date: 13 Oct 2026. Owner of this step: the friend, who holds the Pinpoint key and has tested the API.

Requests can now carry a location: a pin from the caller's phone (GPS or a tap on the map), or an address. Addresses
go to **Pinpoint** on the server. Everything around Pinpoint is built and tested. The one thing left is to make the
request match the call you already tested. Contract: [`contract/api.md`, "Locating a request (D25)"](../../contract/api.md).

## What is already done

| Piece | File | Status |
|---|---|---|
| Location resolver: snap a point to area, segment and nearest landmark | `api/location/resolve.py`, `api/location/geo.py` | Done, tested |
| Pinpoint adapter (key loading, reply parsing, fallbacks) | `api/location/pinpoint.py` | Done, **request shape is a guess** |
| Stand-in when there is no key: made-up demo addresses + "zone + landmark" text | `contract/seed/addresses.synthetic.json` | Done |
| `POST /api/locate` preview; `location` on intake and approve | `api/main.py`, `api/server/memory.py` | Done, tested |
| Exact pickup only for the coordinator and the team that takes the job | `api/views/team.py` (unchanged rule) | Tested |
| Call page (GPS / map pin / address) and desk "Address from the call" | `web/src/features/intake`, `web/src/features/desk` | In progress (UI) |

## What you need to do

1. **Fix the request in one function.** Open `api/location/pinpoint.py` and edit `_request(text, key)` so it
   matches the call you tested:
   - the endpoint URL (or set `PINPOINT_URL` instead of editing code);
   - the parameter names for the address text and the key, or the auth header if the key goes in a header;
   - where the results list is in the reply.

   `_request` must return a list of result dicts. `_point(item)` already reads `lat`/`lng`, `lat`/`lon`,
   `latitude`/`longitude`, or the same inside `location`. If Pinpoint uses other names, change `_point` too.
   The match level is read from `level`, `precision` or `type` and mapped to `house`, `street` or `area`. Adjust the
   mapping in `geocode` if Pinpoint's levels have other names.
2. **Save the key locally, never in Git.** Add one line to `~/.config/reachpoint/env` (the file that already holds
   the Gemini key; it is outside the repo):

   ```
   PINPOINT_API_KEY=<your key>
   ```

   Optional, if the endpoint differs from the default: `PINPOINT_URL=<endpoint>`.
3. **Run the tests.** They mock Pinpoint, so they never use the key or the network:

   ```bash
   .venv/bin/python -m pytest -q api/tests/test_location.py
   ```

   Then add one test that feeds `_request` a copy of a **real reply shape** (with made-up coordinates) and checks
   that `geocode` returns the right point and precision.
4. **Try it live, with a made-up address only**, using the server:

   ```bash
   REACHPOINT_AI=off .venv/bin/python -m uvicorn api.main:app --port 8080
   ```

   ```bash
   curl -s -X POST localhost:8080/api/locate -H 'Content-Type: application/json' -d '{"location":{"kind":"address","text":"12/3 ซอยหลังตลาดกิมหยง หาดใหญ่"}}'
   ```

   Check that `provider` is `"pinpoint"` (not `"stand-in"`), that `status` is `"located"`, and that `segmentId`
   is a Hat Yai segment.
5. **For Cloud Run:** put the key in Secret Manager as `pinpoint-api-key` and pass it to the service as the
   `PINPOINT_API_KEY` environment variable (`--set-secrets PINPOINT_API_KEY=pinpoint-api-key:latest`). The deploy
   script will get this line when we deploy.

## Rules to keep

- **Server side only.** The key never goes to the browser, and the browser never calls Pinpoint directly.
- **Only made-up addresses** are sent to Pinpoint, during development and in the demo
  ([data handling](../collaboration/data-handling.md)).
- **Never log** the key or the address text. `geocode` swallows errors and returns `None` so nothing leaks.
- **If Pinpoint fails or finds nothing,** the stand-in is tried next. If that also fails, the result is
  `unlocated`, and the coordinator picks the landmark by hand. A request is never dropped.
- **Show precision honestly.** Thai addresses often match the street, not the house. Keep `street` or `area` when
  that is what Pinpoint returns.

## How it behaves

| Input | Result |
|---|---|
| Map tap inside Hat Yai | `located`, `caller pin (map)`, precision `street` |
| GPS inside Hat Yai, accuracy ≤ 30 m | `located`, `caller pin (GPS)`, precision `house` |
| GPS outside the demo area | `outside_area`, no point kept (the phone also checks before sending) |
| Address Pinpoint matches | `located`, `Pinpoint address match` / `Pinpoint: street level` / `Pinpoint: area only` |
| No key, or a made-up demo address | the stand-in list, `demo address list (Pinpoint stand-in)` |
| Nothing matches | `unlocated`; the coordinator picks the landmark |

When you are done, tick task 0.6 and the "Location resolver" line in [build-week tasks](build-week-tasks.md), and
open a PR with your change to `pinpoint.py` and the new test.
