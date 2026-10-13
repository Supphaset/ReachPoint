# ReachPoint on Cloud Run: one service serving the web app and the API (contract/api.md).
# Build: gcloud builds submit --tag REGION-docker.pkg.dev/PROJECT/reachpoint/app   (see scripts/deploy.sh)

FROM node:20-slim AS web
WORKDIR /src/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
COPY contract/ ../contract/
COPY data/ ../data/
ENV VITE_DATA=api
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt
COPY api/ api/
COPY contract/ contract/
# The whole Hat Yai package (map layers for location lookup, exposure, rain, gauge; 2.6 MB) and the replay generator.
COPY data/hy-2025-11/ data/hy-2025-11/
COPY data/surge.py data/packages.py data/
COPY --from=web /src/web/dist web/dist
ENV PORT=8080 REACHPOINT_CLOCK=demo
CMD exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
