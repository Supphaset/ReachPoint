#!/usr/bin/env python3
"""Append synthetic five-field forms to a local demo through the caller API."""

import argparse
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from uuid import uuid4


FIXTURE = Path(__file__).resolve().parents[1] / "contract/fixtures/callers.form.synthetic.json"
FORM_FIELDS = ("phone_number", "type", "location", "people_details", "situation_details")


def request(base_url, path, body=None):
    payload = None if body is None else json.dumps(body).encode("utf-8")
    req = Request(base_url + path, data=payload, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=90) as response:
        return json.load(response)


def signature(row):
    # Shared phone numbers do not identify a household or a request.
    return tuple(row.get(field) for field in FORM_FIELDS)


def seed(base_url):
    examples = json.loads(FIXTURE.read_text(encoding="utf-8"))
    for example in examples:
        if set(example) != set(FORM_FIELDS) or example["phone_number"] != "0000000000":
            raise ValueError("The fixture must contain only the five form fields and the fake demo phone.")
        if example["type"] not in {"food", "evacuation"} or not example["location"]:
            raise ValueError("Each example needs a help type and Google Maps link.")
    known = {signature(row) for row in request(base_url, "/api/desk")["callers"]}
    added = 0
    for example in examples:
        key = signature(example)
        if key in known:
            continue
        session = request(base_url, "/api/callers/sessions", {})
        submitted = request(base_url, f"/api/callers/sessions/{session['sessionId']}/form", {
            **example, "expectedRevision": session["revision"], "submissionId": str(uuid4()),
        })
        if not submitted.get("sent"):
            raise ValueError("The API did not confirm the synthetic request.")
        print(f"Added {submitted['sent']['reportId']}")
        known.add(key)
        added += 1
    print(f"Added {added}; already present {len(examples) - added}. Existing requests preserved.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8768")
    args = parser.parse_args()
    url = urlsplit(args.base_url)
    if url.scheme not in {"http", "https"} or url.hostname not in {"localhost", "127.0.0.1", "::1"}:
        parser.error("Use the local demo server URL.")
    if url.username or url.password or url.query or url.fragment or url.path not in {"", "/"}:
        parser.error("Use a server origin without credentials, path, query or fragment.")
    try:
        seed(args.base_url.rstrip("/"))
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as error:
        # Avoid printing response bodies or submitted caller details.
        print(f"Seeding stopped ({type(error).__name__}). Check the local server; rerun to skip saved examples.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
