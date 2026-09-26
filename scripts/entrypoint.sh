#!/bin/sh
set -eu
mkdir -p /data /srv/public /srv/public/upload /var/log/supervisor /etc/caddy
cp -a /app/static/upload/. /srv/public/upload/
python /app/scripts/generate_runtime.py
if [ "${RSS_AUTH_MODE:-none}" = "none" ]; then
  echo "WARNING: RSS_AUTH_MODE=none; write/agent interfaces are unauthenticated. Intended for trusted labs." >&2
fi
exec /usr/local/bin/supervisord -c /app/supervisor/supervisord.conf
