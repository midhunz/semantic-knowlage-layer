# Semantic Knowledge Layer

A metadata catalog and semantic layer over an Iceberg/Parquet data lake (via Trino). It pulls technical metadata, lets stewards add the business meaning an LLM needs, and serves the result to agents over REST, MCP, and prompt-ready exports.

## Run (development)

```bash
# 1. Dev lake (Postgres + S3 mock + Trino/Iceberg) – optional if you have your own Trino
docker compose up -d
trino --server localhost:8080 --catalog lake -f dev/seed/seed.sql   # sample star schema (needs the Trino CLI)

# 2. Backend (SQLite by default; migrations run automatically in development)
cd backend && python3.12 -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/uvicorn app.main:app --reload --port 8010      # API docs: http://localhost:8010/docs
make test        # in-memory SQLite      |  make test-pg   # real Postgres (docker compose up -d postgres)

# 3. UI
cd frontend && npm install && npm run dev                 # http://localhost:5173  (proxy target: VITE_API, default :8010)
```

`python -m app.cli` provides `check`, `migrate`, `create-admin`, `reset-password` and `backup`.
**Production:** see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) (Docker, Postgres, HTTPS, migrations, backups).

## Workflow
1. **Sources** – add a Trino source (catalog `lake`) and click *Sync metadata*. Re-sync never overwrites curated fields; new or changed tables/columns land in the **review queue**.
2. **Tables** – open a table: set type (fact/dimension/…), grain, description, caveats; per column set description, role (measure/dimension/time/identifier), semantic type, default aggregation, synonyms, allowed values, PK/PII flags.
3. **Metrics / Glossary / Dimensions** – define governed business metrics (SQL expression), terms with synonyms and dimensions. Everything new or edited is a **draft**; submit it, and a reviewer approves or rejects it (Pending changes → Awaiting review). Agents only see approved content ([docs/METADATA_LIFECYCLE.md](docs/METADATA_LIFECYCLE.md)).
4. **Publish** a table. Only `published` content (and non-PII example values) is visible to agents.

## Working at scale (hundreds of tables, several sources)
- **Navigate:** left tree is Source → Schema with counts and EN/عربي coverage dots; the **Catalog** grid is server-side (search, filters, sort, pagination) and its filters live in the URL, so any view can be bookmarked or shared.
- **Triage:** Overview shows coverage by source, domain and type; quick filters: needs review, no description, no grain, no Arabic, columns undocumented, unpublished.
- **Bulk edit:** tick rows (or "select all N matching this filter") → set type / domain / owner, mark reviewed, or publish.
- **Column dictionary:** columns grouped by name across every source; describe `customer_id` once (EN + AR) and apply it to every table, filling only blanks or overwriting.
- **Spreadsheet round-trip:** export columns/tables CSV (UTF-8 with BOM so Arabic opens correctly in Excel), edit, import back; empty cells never overwrite.
- **Bilingual:** every semantic text field has an Arabic twin; header toggle EN / EN + عربي / عربي. Agents choose `lang=en|ar|both`; Arabic search ignores diacritics and alef/ya/ta-marbuta variants.
- Tables are addressed as `source.schema.table` (two-part `schema.table` works only while unambiguous).

## How metadata changes
New or sensitive-looking columns are **quarantined** (hidden from agents) until a steward releases them, and edits to **published** tables are **staged** as pending revisions that are reviewed and published as numbered versions (with history and restore). See [docs/METADATA_LIFECYCLE.md](docs/METADATA_LIFECYCLE.md).

## Dimensions
Business concepts like *person category* with their values, English/Arabic labels, the words people use for each value, families, an "applies to" rule, and links to the columns that hold them. Agents resolve what people say with `resolve_value("residents")` → `EXPAT`. See [docs/DIMENSIONS.md](docs/DIMENSIONS.md).

## Administration (Settings)
Open **Settings** (administrators only).
- **First run:** until an administrator exists the catalog is *open* (a yellow bar says so). Click **Secure this catalog** to create the first admin; after that everyone must sign in.
- **Roles:** *Viewer* browses; *Steward* documents, publishes and syncs; *Administrator* also manages settings, users, keys and webhooks. The last active admin can't be demoted, deactivated or deleted. Temporary passwords force a change at first sign-in.
- **API keys:** one per consuming app. Scopes (`agent:read`, `catalog:read`, `catalog:write`), optional restriction to specific **domains**, expiry, rotate, revoke. The secret is shown once; only its SHA-256 is stored. Send it as `X-API-Key` or `Authorization: Bearer`.
- **Agent defaults:** default language, token budget, and whether PII columns are hidden completely or only their values.
- **Publishing rules:** require "reviewed" first and/or a minimum documentation % — enforced for single, bulk and CSV publishing.
- **Webhooks:** `table.published`, `table.unpublished`, `catalog.synced`; JSON `POST` signed with `X-SL-Signature: sha256=<HMAC of body>`. One attempt, 5 s timeout (a nudge to re-read, not a queue).
- **Audit log:** every catalog change with the signed-in user (or `key:<name>`) as the actor.

## Agent access
- **REST** — send `X-API-Key: sl_live_…` (or sign in): `GET /agent/search?q=`, `/agent/tables/{source.schema.table}/context?lang=en|ar|both&max_tokens=2000`, `/agent/export?domain=`, `/agent/glossary/resolve?term=`, `/agent/metrics`, `/agent/sample-queries`. A domain-restricted key only sees tables, metrics and samples inside its domains. `lang` and `max_tokens` fall back to the admin defaults.
- **MCP** (stdio): `cd backend && .venv/bin/python -m app.mcp_server` — tools: `list_tables`, `search_catalog_tool`, `describe_table`, `get_join_path`, `list_metrics`, `resolve_term`, `get_sample_queries`, `list_dimensions`, `describe_dimension`, `resolve_value`. It runs where it can read the catalog database directly (no API key, so no per-key domain limits) but follows the admin defaults for language, size and PII. Requires `mcp<2`.

## Lake credentials
Use a read-only Trino user. Passwords are never stored in the catalog: set `config.password_env` to the name of an env var.

## Production notes
- See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). Cookies are `Secure` automatically over HTTPS; the login throttle is stored in the database.
- Webhook URLs are admin-controlled and can point at internal addresses — keep Settings to people you trust.
- `SL_API_KEYS` (env) still works as a legacy agent-only key list.

## Not yet built
Athena/Glue connector, role-based edit rights, metric SQL dry-run validation, relationship/sample-query UI pages (API exists), pgvector semantic search.
