# AI finishing prompt — rss-publisher-agent (continuation)

You are continuing the release-finishing pass for `bigbatmanorg/rss-publisher-agent`.
A previous session did substantial work. **Read `STATUS.md` first** — it is the
authoritative record of what is done, what is broken, and the exact next action.

This repository is intentionally thin. Do not move deterministic RSS/persistence/asset
logic out of `bigbatmanorg/rss-publisher-mcp` into this repo. The agent repo owns
behavior, protocol adapters, Caddy/public routing, the upload UI, runtime discovery and
one-container packaging.

Use `specs/ARCHITECTURE.md` and `specs/RELEASE_GATES.md` as normative.
The MCP repo is published at `https://github.com/bigbatmanorg/rss-publisher-mcp`
(**private**) and the dev copy is at
`/home/toor/projects/rss-publisher-mcp-v0.1.0/rss-publisher-mcp/`.

## State at handoff

### Already done (do not redo)

- Pinned `DOCKER_AGENT_VERSION=v1.144.0` with verified amd64/arm64 SHA-256.
- Pinned `RSS_PUBLISHER_MCP_REF=v0.1.0` (no longer `main`).
- Fixed `uv run pytest` (setuptools `packages = []`).
- Fixed supervisord publisher-mcp orphan/port-conflict crash loop.
- Fixed `.env` embeddings model/dimensions.
- Fixed opaque MCP tool schemas in the MCP repo (typed `FeedEntry`/`EntryPatch`/
  `BatchOperation`/`FeedConfig` + `_payload()` helper).
- Added a 14-tool `tools:` filter to `agent.yaml` (prefixed `publisher_*` names) because
  the model stops emitting tool calls at 16 tools.
- Hardened the agent instruction with a `TOOL CALLING RULES` block.
- Verified natively: all 7 processes up, `/readyz` ready, public surface, private MCP
  (404 on `/publisher/mcp`), Docker Agent remote private MCP connection, `--dry-run`,
  `serve mcp`/`a2a`/`chat`, A2A card rewrite, real end-to-end publish.

### Immediate blockers (resolve first)

1. **MCP repo is private** -> the Dockerfile's anonymous `git+https` clone fails, so the
   container build is unverified. Choose a strategy: build secret/`--secret` git token,
   vendored wheel, or make the repo public.
2. ~~The `v0.1.0` tag predates the schema fix.~~ **RESOLVED.** The MCP schema fix was
   committed (`e20432a`), pushed to `main`, and `v0.1.0` was moved to that commit and
   force-pushed. Verified the tag contains `EntryPatch`/`_payload`; MCP `pytest` passes.

### Failing behavior gates (5 of 14 scenarios)

See `STATUS.md` for detail. Most serious: the agent **fabricated a Nobel Prize entry**
instead of refusing/asking when asked to publish with a missing source URL. Also failing:
continuity_key status update, active-update GUID preservation, correction lifecycle,
and batch using `publish_batch`. These are model-behavior issues with the configured
`brain` model; consider a stronger `AGENT_MODEL`, stronger instructions, or a
deterministic pre-check.

## Remaining tasks

1. Resolve the private-repo build path; build the container for amd64 and arm64
   (or at minimum validate both download/build paths).
2. Fix the 5 failing behavior scenarios; re-run `/tmp/appliance/scenarios.py`.
3. `RSS_AUTH_MODE=none` and `bearer` end-to-end through Caddy.
4. Uploads from both `/upload/` and the direct HTTP API.
5. Confirm the deterministic Publisher MCP stays private and is not routed publicly.
6. `/agent/mcp`, A2A and `/v1/chat/completions` all drive the same agent behavior.
7. Treat Docker Agent A2A as evolving: advertise/test only what v1.144.0 implements.
8. Embeddings enabled (verify vectors generated and used for active-entry matching)
   and disabled (verify correct degraded behavior).
9. Verify `.env` URL injection: changing only `RSS_PUBLIC_BASE_URL` updates agent
   instructions, discovery, feed URLs and asset URLs coherently.
10. Tick the checkboxes in `specs/RELEASE_GATES.md` and keep `STATUS.md` current.

Do not declare release-ready until every required gate is either passed or explicitly
documented as an upstream blocker with a reproducible test.

## Local test harness (reuse it)

The appliance was run natively because `/srv` and `/etc/caddy` need sudo. Harness in
`/tmp/appliance/`:

- `run.sh` — loads repo `.env`, overrides paths to `/tmp/appliance`, regenerates runtime
  files, starts supervisord.
- `supervisord.local.conf` — same programs as the repo, local paths.
- `gen_local_runtime.py` — generates Caddyfile + manifest with local paths.
- `scenarios.py` — behavior scenario suite (state-based assertions).
- `chat.sh` — one-shot chat request helper.

Reset between runs:

```bash
pkill -f supervisord.local.conf; pkill -f rss-publisher-mcp; pkill -f rss-publisher-api
pkill -f appliance_runtime.py; pkill -f 'docker-agent serve'; pkill -f 'caddy run'
sleep 3
cd /tmp/appliance && rm -rf data logs public && mkdir -p data logs public
nohup ./run.sh > /tmp/appliance/supervisord.out 2>&1 &
sleep 14 && curl -sS http://localhost:8080/readyz
```

## MCP repo changes made this session (committed + tagged)

`src/rss_publisher/models.py` — added `EntryPatch`, `BatchOperation` models.
`src/rss_publisher/mcp_server.py` — typed tool params + `_payload()` helper.
Committed as `e20432a` on `main`; `v0.1.0` moved to that commit and force-pushed.
