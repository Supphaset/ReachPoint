#!/usr/bin/env bash
# Run from the repo root after firebase login (or npx -y firebase-tools@13 login).
set -euo pipefail
npx -y firebase-tools@13 deploy --only hosting --project "${PROJECT:-reachpoint-main}"
