#!/usr/bin/env bash
# Copy the keys from ~/.config/reachpoint/env (outside the repo) into Secret Manager, once per project.
# Each value goes straight from the file to gcloud through a pipe: it is never printed, logged or put in Git.
#   GEMINI_API_KEY          -> gemini-api-key      (required)
#   PINPOINT_API_KEY        -> pinpoint-api-key    (optional)
#   GOOGLE_MAPS_BROWSER_KEY or VITE_GOOGLE_MAPS_KEY -> maps-browser-key (optional; a browser key, locked to our sites)
# Running it again adds a new version of each secret.
set -euo pipefail

PROJECT="${PROJECT:-$(gcloud config get-value project)}"
ENV_FILE="${ENV_FILE:-$HOME/.config/reachpoint/env}"
gcloud services enable secretmanager.googleapis.com --project "$PROJECT"

put() {  # put secret-name VAR [OTHER_VAR]: the first variable found in the file
  local name="$1" value="" var
  shift
  for var in "$@"; do
    [ -n "$value" ] || value="$(grep -m1 "^$var=" "$ENV_FILE" | cut -d= -f2- || true)"
  done
  if [ -z "$value" ]; then echo "skip $name: $* not in $ENV_FILE"; return; fi
  if gcloud secrets describe "$name" --project "$PROJECT" >/dev/null 2>&1; then
    printf '%s' "$value" | gcloud secrets versions add "$name" --project "$PROJECT" --data-file=- >/dev/null
  else
    printf '%s' "$value" | gcloud secrets create "$name" --project "$PROJECT" --replication-policy automatic --data-file=- >/dev/null
  fi
  echo "saved $name"
}

put gemini-api-key GEMINI_API_KEY
put pinpoint-api-key PINPOINT_API_KEY
put maps-browser-key GOOGLE_MAPS_BROWSER_KEY VITE_GOOGLE_MAPS_KEY
