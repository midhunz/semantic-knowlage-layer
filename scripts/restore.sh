#!/usr/bin/env bash
# Restore a dump into the production database. DESTROYS the current contents.
# Usage: scripts/restore.sh backups/semantic_layer-YYYYMMDD-HHMMSS.dump [--yes]
set -euo pipefail
cd "$(dirname "$0")/.."
FILE="${1:?usage: scripts/restore.sh <dump file> [--yes]}"
[ -f "$FILE" ] || { echo "No such file: $FILE" >&2; exit 1; }
DC=(docker compose -f docker-compose.prod.yml)

if [ "${2:-}" != "--yes" ]; then
  read -r -p "This REPLACES the live database with $FILE. Type 'restore' to continue: " ANSWER
  [ "$ANSWER" = "restore" ] || { echo "Aborted."; exit 1; }
fi

"${DC[@]}" exec -T db pg_restore --list < "$FILE" > /dev/null || { echo "Not a valid dump file" >&2; exit 1; }
echo "Stopping the app…"
"${DC[@]}" stop app proxy
echo "Restoring…"
"${DC[@]}" exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner --exit-on-error' < "$FILE"
echo "Applying any newer migrations…"
"${DC[@]}" run --rm migrate
echo "Starting the app…"
"${DC[@]}" start app proxy
echo "Restore complete."
