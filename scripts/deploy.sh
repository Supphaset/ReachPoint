#!/usr/bin/env bash
# Deploy ReachPoint to Cloud Run (one service: web + API). Run from the repo root after:
#   gcloud auth login && gcloud config set project YOUR_PROJECT_ID
#   scripts/put-secrets.sh   # once: copies the keys from ~/.config/reachpoint/env into Secret Manager
# Needs on the project: Cloud Run, Cloud Build, Artifact Registry and Secret Manager APIs, and a billing account.
set -euo pipefail

PROJECT="${PROJECT:-$(gcloud config get-value project)}"
REGION="${REGION:-asia-southeast1}"   # Singapore, closest to Hat Yai
SERVICE="${SERVICE:-reachpoint}"
REPO="${REPO:-reachpoint}"
IMAGE="$REGION-docker.pkg.dev/$PROJECT/$REPO/app:$(git rev-parse --short HEAD)"

echo "Project $PROJECT · region $REGION · image $IMAGE"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com --project "$PROJECT"
gcloud artifacts repositories describe "$REPO" --location "$REGION" --project "$PROJECT" >/dev/null 2>&1 ||
  gcloud artifacts repositories create "$REPO" --repository-format docker --location "$REGION" --project "$PROJECT"

# The service runs as the default compute identity; it may read the keys, nothing else.
RUNNER="$(gcloud projects describe "$PROJECT" --format 'value(projectNumber)')-compute@developer.gserviceaccount.com"
SECRETS="GEMINI_API_KEY=gemini-api-key:latest"
for pair in "PINPOINT_API_KEY=pinpoint-api-key" "GOOGLE_MAPS_BROWSER_KEY=maps-browser-key"; do
  name="${pair#*=}"
  gcloud secrets describe "$name" --project "$PROJECT" >/dev/null 2>&1 && SECRETS="$SECRETS,${pair}:latest"
done
for name in gemini-api-key pinpoint-api-key maps-browser-key; do
  gcloud secrets describe "$name" --project "$PROJECT" >/dev/null 2>&1 &&
    gcloud secrets add-iam-policy-binding "$name" --project "$PROJECT" --member "serviceAccount:$RUNNER" \
      --role roles/secretmanager.secretAccessor >/dev/null
done

gcloud builds submit --tag "$IMAGE" --project "$PROJECT" .

# One instance keeps the in-memory demo rooms consistent; min 1 keeps it warm for judges (a restart still resets
# the demo). No CPU throttling: the triage agent and zone briefings finish after the reply is sent.
gcloud run deploy "$SERVICE" --image "$IMAGE" --region "$REGION" --project "$PROJECT" \
  --allow-unauthenticated --max-instances 1 --min-instances 1 --no-cpu-throttling --memory 1Gi --cpu 1 \
  --set-env-vars REACHPOINT_CLOCK=demo --set-secrets "$SECRETS"

URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT" --format 'value(status.url)')"
echo "$URL"
echo "Add $URL/* to the allowed websites of the Maps browser key (APIs & Services > Credentials) if the map stays blank."
