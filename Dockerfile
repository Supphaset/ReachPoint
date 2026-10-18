# ReachPoint on Cloud Run: one service serving the web app and the API (api/v2/routes.py).
# Build: gcloud builds submit --tag REGION-docker.pkg.dev/PROJECT/reachpoint/app   (see scripts/deploy.sh)

FROM node:20-slim AS web
WORKDIR /src/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
COPY data/ ../data/
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt
COPY api/ api/
# The Hat Yai inputs, cached scenario and flood-model outputs used by v2.
COPY data/hy-2025-11/ data/hy-2025-11/
COPY --from=web /src/web/dist web/dist
ENV PORT=8080
CMD exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
