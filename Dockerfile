# syntax=docker/dockerfile:1
# One image serves the API and the built web UI. Build from the repository root:  docker build -t semantic-layer .

# ---- 1. build the web UI -------------------------------------------------------------------------
FROM node:20-alpine AS ui
WORKDIR /ui
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- 2. runtime ----------------------------------------------------------------------------------
FROM python:3.12-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SL_ENV=production SL_STATIC_DIR=/app/static
WORKDIR /app

# Dependencies first so this layer is cached until pyproject.toml changes. The app runs from source in
# /app (not as an installed package) so alembic/ and alembic.ini sit next to it.
COPY backend/pyproject.toml ./
RUN python -c "import tomllib; print('\n'.join(tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']))" > /tmp/req.txt \
 && pip install -r /tmp/req.txt && rm /tmp/req.txt

COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./
COPY --from=ui /ui/dist ./static

RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin app
USER app
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=4s --start-period=20s --retries=4 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=3).status == 200 else 1)"

# --proxy-headers lets the app see the original scheme (https) from the reverse proxy, which drives the Secure cookie.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY:-2} --proxy-headers --forwarded-allow-ips \"${FORWARDED_ALLOW_IPS:-*}\" --no-server-header"]
