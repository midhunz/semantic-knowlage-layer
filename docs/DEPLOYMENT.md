# Deploying the Semantic Layer

A production install is one `docker compose` stack: **Postgres**, a one-shot **migration**, the **app** (API + web UI), a **TLS proxy** (Caddy) and a **backup** job.

## 1. Quick start

```bash
cp .env.example .env                       # then edit it
#   POSTGRES_PASSWORD=$(openssl rand -hex 24)
#   SL_DOMAIN=semantic.example.com         # a real domain gives automatic HTTPS (ports 80/443 must reach this host)
docker compose -f docker-compose.prod.yml up -d --build

# create the first administrator (production has no browser setup and no anonymous mode)
docker compose -f docker-compose.prod.yml exec app python -m app.cli create-admin --email you@example.com
```

Open `https://<your domain>` and sign in. To trial it without a domain, set `SL_DOMAIN=:80` (plain HTTP) and `SL_HTTP_PORT=8088`.

## 2. What "production mode" changes

`SL_ENV=production` is set by the image. The app then **refuses to start** if the database is SQLite, `SL_COOKIE_SECURE=never`, or `SL_REQUIRE_AUTH=false`, and:

| Area | Behaviour |
|---|---|
| Access | No anonymous mode. Until an admin exists every request is `401`; the sign-in page says how to create one. Browser setup is disabled. |
| Cookies | `HttpOnly`, `SameSite=Lax`, and `Secure` whenever the request arrived over HTTPS (also behind the proxy, via `X-Forwarded-Proto`). HSTS is sent over HTTPS. |
| Headers | CSP, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy`; API responses are `no-store`. |
| Errors | Unhandled errors return a generic 500 with a `request_id` (also in the logs), never a stack trace. API docs (`/docs`, `/openapi.json`) are off. |
| Login throttle | 5 failures / 5 min per email, **stored in the database**, so it holds across workers and restarts. |
| Schema | The app only *verifies* the schema is at the expected version; migrations run in the separate `migrate` step. |
| Logs | JSON lines on stdout with request ids. The database password is masked. |
| Probes | `/health` (liveness, no DB) and `/ready` (DB reachable **and** schema current). The container healthcheck and proxy use `/ready`. |

## 3. Configuration

All settings are `SL_*` environment variables (see `.env.example` for the ones the compose file passes through).

| Variable | Default | Meaning |
|---|---|---|
| `SL_DATABASE_URL` | SQLite file (dev) | `postgresql://user:pass@host:5432/db` (compose builds it from `POSTGRES_*`) |
| `SL_COOKIE_SECURE` | `auto` | `auto` / `always` / `never` |
| `SL_REQUIRE_AUTH` | `true` in production | refuse anonymous access even with no users |
| `SL_CORS_ORIGINS` | empty in production | only needed if the UI is hosted on a different origin |
| `SL_BOOTSTRAP_ADMIN_EMAIL` / `_PASSWORD` | – | create the first admin at startup; remove the password afterwards |
| `SL_LOG_JSON`, `SL_LOG_LEVEL` | `false`, `INFO` | |
| `WEB_CONCURRENCY` | `2` | uvicorn worker processes |

## 4. Upgrading

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build   # rebuilds, runs migrations, restarts the app
```

The `migrate` service runs `python -m app.cli migrate` before the app starts; the app will not start against an out-of-date schema. **Take a backup first** (`make backup`).

When you change a model, create a migration and commit it:

```bash
make revision m="add foo column"      # autogenerates backend/alembic/versions/…; review it, then commit
```

A test fails if the models and migrations disagree, so a forgotten migration is caught in CI.

**Databases created before migrations existed** (the old auto-create startup) are adopted automatically by `migrate`: missing tables/columns are added and the database is stamped at the baseline; no data is touched.

## 5. Backups and restore

* The `backup` service runs `pg_dump` every `BACKUP_INTERVAL_HOURS` (default 24) into `./backups/`, checks each dump is readable, and deletes dumps older than `BACKUP_KEEP_DAYS` (default 14).
* On demand: `make backup` (or `scripts/backup.sh [dir]`).
* Restore: `make restore f=backups/semantic_layer-YYYYMMDD-HHMMSS.dump` (asks you to type `restore`; use `--yes` to skip). It validates the file first, stops the app, restores, applies newer migrations, and starts the app again. A corrupt file is rejected before anything is stopped.

> **A backup on the same machine is not a disaster-recovery plan.** Copy `./backups/` off the host (object storage, another server). Restore into a scratch environment now and then to prove the backups work.

SQLite (development only): `python -m app.cli backup --out backups` makes a consistent copy while the app runs.

## 6. Operations

```bash
python -m app.cli check                       # config + DB + schema status (exit 1 on problems)
python -m app.cli reset-password --email you@example.com     # temporary password, must be changed at sign-in; ends their sessions
docker compose -f docker-compose.prod.yml exec app python -m app.cli <command>
docker compose -f docker-compose.prod.yml logs -f app
```

If every administrator is locked out, `reset-password` on the server is the recovery path.

## 7. Security checklist

- [ ] `.env` is not in git and only readable by the deploy user; `POSTGRES_PASSWORD` is random.
- [ ] `SL_DOMAIN` is a real domain with working HTTPS; HTTP redirects to HTTPS (Caddy does this automatically).
- [ ] First admin created with the CLI; `SL_BOOTSTRAP_ADMIN_PASSWORD` removed if you used it.
- [ ] A **second** admin exists (Settings → Users) so a locked-out admin isn't an emergency.
- [ ] Backups copied off-host; a restore has been rehearsed.
- [ ] Source credentials: lake passwords are never stored in the catalog — use `password_env` and set that variable on the app container.
- [ ] Webhook URLs are admin-controlled and can point at internal addresses; keep Settings to trusted people.

## 8. Not included (decide for your environment)

High-availability Postgres or managed Postgres (point `SL_DATABASE_URL` at it and drop the `db` service), a secrets manager, SSO, rate limiting at the proxy, centralized log shipping and metrics/alerting, and automated off-host backup copies.
