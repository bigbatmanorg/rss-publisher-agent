#!/bin/sh
set -eu
BASE="${RSS_SMOKE_BASE_URL:-http://localhost:8080}"
TOKEN="${RSS_API_TOKEN:-}"
AUTH=""
if [ -n "$TOKEN" ]; then AUTH="Authorization: Bearer $TOKEN"; fi

curl -fsS "$BASE/healthz" >/dev/null
curl -fsS "$BASE/readyz" >/dev/null
curl -fsS "$BASE/feed.xml" >/dev/null
curl -fsS "$BASE/upload/" >/dev/null
curl -fsS "$BASE/.well-known/rss-publisher.json" >/dev/null

tmp="$(mktemp)"
printf 'rss-publisher appliance smoke\n' > "$tmp"
if [ -n "$AUTH" ]; then
  asset="$(curl -fsS -H "$AUTH" -F "file=@$tmp;type=text/plain" "$BASE/api/v1/assets")"
else
  asset="$(curl -fsS -F "file=@$tmp;type=text/plain" "$BASE/api/v1/assets")"
fi
rm -f "$tmp"
printf '%s\n' "$asset" | grep -q 'asset_id'

echo "PASS appliance HTTP/static/upload smoke"
echo "NOTE: agent protocol/model behavior is covered by the release integration suite because it requires a live configured model endpoint."
