#!/usr/bin/env bash
# Deploy ReachPoint to Cloud Run (one service: web + API). Run from the repo root after:
#   gcloud auth login && gcloud config set project YOUR_PROJECT_ID
# Needs on the project: Cloud Run, Cloud Build and Artifact Registry APIs, and a billing account (the free trial works).
set -euo pipefail

PROJECT="${PROJECT:-$(gcloud config get-value project)}"
REGION="${REGION:-asia-southeast1}"   # Singapore, closest to Hat Yai
SERVICE="${SERVICE:-reachpoint}"
REPO="${REPO:-reachpoint}"
IMAGE="$REGION-docker.pkg.dev/$PROJECT/$REPO/app:$(git rev-parse --short HEAD)"

echo "Project $PROJECT · region $REGION · image $IMAGE"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project "$PROJECT"
gcloud artifacts repositories describe "$REPO" --location "$REGION" --project "$PROJECT" >/dev/null 2>&1 ||
  gcloud artifacts repositories create "$REPO" --repository-format docker --location "$REGION" --project "$PROJECT"

gcloud builds submit --tag "$IMAGE" --project "$PROJECT" .

# One instance keeps the in-memory demo consistent (every request sees the same records). Scale to zero when idle.
gcloud run deploy "$SERVICE" --image "$IMAGE" --region "$REGION" --project "$PROJECT" \
  --allow-unauthenticated --max-instances 1 --min-instances 0 --memory 512Mi --cpu 1 \
  --set-env-vars REACHPOINT_CLOCK=demo

gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT" --format 'value(status.url)'
