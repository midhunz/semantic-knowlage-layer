#!/usr/bin/env bash
# Runs inside the `backup` container: dump, verify, prune, sleep, repeat.
set -uo pipefail
INTERVAL=$(( ${BACKUP_INTERVAL_HOURS:-24} * 3600 ))
KEEP_DAYS=${BACKUP_KEEP_DAYS:-14}
mkdir -p /backups

while true; do
  STAMP=$(date -u +%Y%m%d-%H%M%S)
  FILE="/backups/semantic_layer-${STAMP}.dump"
  if pg_dump -Fc -f "${FILE}.partial" && pg_restore --list "${FILE}.partial" > /dev/null; then
    mv "${FILE}.partial" "${FILE}"
    echo "$(date -u +%FT%TZ) backup ok: ${FILE} ($(stat -c %s "${FILE}") bytes)"
    find /backups -name 'semantic_layer-*.dump' -mtime +"${KEEP_DAYS}" -print -delete
  else
    rm -f "${FILE}.partial"
    echo "$(date -u +%FT%TZ) BACKUP FAILED" >&2
  fi
  sleep "${INTERVAL}"
done
