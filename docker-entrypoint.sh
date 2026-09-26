#!/bin/sh
set -eu

mkdir -p /app/config /app/downloads /app/temp

if [ ! -f /app/config/settings.json ]; then
    # The first invocation creates Orpheus' complete default configuration.
    python3 /app/orpheus.py settings refresh || true
fi

python3 /app/scripts/configure.py
chmod 0700 /app/config 2>/dev/null || true
chmod 0600 /app/config/settings.json /app/config/loginstorage.bin 2>/dev/null || true

if [ "${1:-}" = "cli" ]; then
    shift
    exec python3 /app/orpheus.py "$@"
fi

exec "$@"
