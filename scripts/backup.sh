#!/usr/bin/env bash
# One-off backup of the production database to ./backups (or the directory given as $1).
# Usage: scripts/backup.sh [dir]        Copy the resulting file OFF this machine as well.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-backups}"; mkdir -p "$OUT"
FILE="$OUT/semantic_layer-$(date -u +%Y%m%d-%H%M%S).dump"
DC=(docker compose -f docker-compose.prod.yml)

"${DC[@]}" exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB"' > "$FILE.partial"
"${DC[@]}" exec -T db pg_restore --list < "$FILE.partial" > /dev/null   # proves the dump is readable
mv "$FILE.partial" "$FILE"
echo "Backup written: $FILE ($(wc -c < "$FILE" | tr -d ' ') bytes)"
