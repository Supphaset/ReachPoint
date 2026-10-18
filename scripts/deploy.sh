#!/usr/bin/env bash
# Deploy ReachPoint to Cloud Run (one service: web + API). Run from the repo root after:
#   gcloud auth login && gcloud config set project YOUR_PROJECT_ID
#   scripts/put-secrets.sh   # once: copies the keys from ~/.config/reachpoint/env into Secret Manager
# Needs on the project: Cloud Run, Cloud Build, Artifact Registry, Secret Manager and Vertex AI APIs, and billing.
# Gemini runs with the paid Gemini API key from Secret Manager (GEMINI_ROUTE=key, the default, tested end to end);
# GEMINI_ROUTE=vertex uses Vertex AI with the service's own identity instead.
# Voice (Gemini Live) is gemini-3.8-live in us-central1, the only single region that serves it; VOICE=off skips it.
set -euo pipefail

PROJECT="${PROJECT:-$(gcloud config get-value project)}"
REGION="${REGION:-asia-southeast1}"   # Singapore, closest to Hat Yai
SERVICE="${SERVICE:-reachpoint}"
VOICE="${VOICE:-on}"
GEMINI_ROUTE="${GEMINI_ROUTE:-key}"
REPO="${REPO:-reachpoint}"
IMAGE="$REGION-docker.pkg.dev/$PROJECT/$REPO/app:$(git rev-parse --short HEAD)"

echo "Project $PROJECT · region $REGION · image $IMAGE"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com aiplatform.googleapis.com --project "$PROJECT"
gcloud artifacts repositories describe "$REPO" --location "$REGION" --project "$PROJECT" >/dev/null 2>&1 ||
  gcloud artifacts repositories create "$REPO" --repository-format docker --location "$REGION" --project "$PROJECT"

# The service runs as the default compute identity: it may call Vertex AI, read the keys and persist demo rooms.
RUNNER="$(gcloud projects describe "$PROJECT" --format 'value(projectNumber)')-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding "$PROJECT" --member "serviceAccount:$RUNNER" \
  --role roles/aiplatform.user --condition None >/dev/null
SECRETS=""
PAIRS=("PINPOINT_API_KEY=pinpoint-api-key" "GOOGLE_MAPS_BROWSER_KEY=maps-browser-key")
[ "$GEMINI_ROUTE" = key ] && PAIRS+=("GEMINI_API_KEY=gemini-api-key")
for pair in "${PAIRS[@]}"; do
  name="${pair#*=}"
  gcloud secrets describe "$name" --project "$PROJECT" >/dev/null 2>&1 && SECRETS="${SECRETS:+$SECRETS,}${pair}:latest"
done
for name in gemini-api-key pinpoint-api-key maps-browser-key; do
  gcloud secrets describe "$name" --project "$PROJECT" >/dev/null 2>&1 &&
    gcloud secrets add-iam-policy-binding "$name" --project "$PROJECT" --member "serviceAccount:$RUNNER" \
      --role roles/secretmanager.secretAccessor >/dev/null
done

gcloud builds submit --tag "$IMAGE" --project "$PROJECT" .

# One instance keeps active demo rooms consistent; Firestore restores v2 rooms after a restart.
# Min 1 keeps it warm for judges. No CPU throttling: the triage agent and zone briefings finish after the reply is sent.
# Live calls stop after five minutes in the app. The longer request timeout leaves time to close cleanly.
# Session affinity keeps a reconnecting caller on the same instance.
ENV="RP_GEMINI_CALLS_15MIN=400,RP_LIVE_MIN_15MIN=45,RP_CLASSIC_ENABLED=0,RP_FIRESTORE=1,REACHPOINT_CLOCK=demo,REACHPOINT_GEMINI=$GEMINI_ROUTE,GOOGLE_CLOUD_PROJECT=$PROJECT,REACHPOINT_VOICE=$VOICE"
ENV="$ENV,GEMINI_LIVE_LOCATION=us-central1,GEMINI_LIVE_MODEL=gemini-3.8-live"
gcloud run deploy "$SERVICE" --image "$IMAGE" --region "$REGION" --project "$PROJECT" \
  --service-account "$RUNNER" --allow-unauthenticated --max 1 --min 1 --max-instances 1 --min-instances 0 --no-cpu-throttling --memory 1Gi --cpu 1 \
  --timeout 900 --session-affinity --set-env-vars "$ENV" ${SECRETS:+--set-secrets "$SECRETS"}

URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT" --format 'value(status.url)')"
echo "$URL"
echo "Add $URL/* to the allowed websites of the Maps browser key (APIs & Services > Credentials) if the map stays blank."
