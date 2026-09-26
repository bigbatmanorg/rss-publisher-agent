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
(**public**) and the dev copy is at
`/home/toor/projects/rss-publisher-mcp-v0.1.0/rss-publisher-mcp/`.

## Git workflow (you are authorized)

You may and should commit and push in both repos as you work. Keep them in sync.

- **MCP repo** (`/home/toor/projects/rss-publisher-mcp-v0.1.0/rss-publisher-mcp`):
  remote `origin` = `https://github.com/bigbatmanorg/rss-publisher-mcp.git`, branch
  `main`. Commit fixes, push to `main`, and when a change affects the agent appliance,
  move/cut the release tag (currently `v0.1.0`) and push it, then bump
  `RSS_PUBLISHER_MCP_REF` in the agent repo to match.
- **Agent repo** (`/home/toor/projects/rss-publisher-agent-v0.1.0/rss-publisher-agent`):
  published at `https://github.com/bigbatmanorg/rss-publisher-agent` (public), remote
  `origin` configured, branch `master`, local and remote in sync. Commit and push freely.
  **GitHub Actions is DISABLED** on this repo until everything works locally — do not
  re-enable it as part of routine work. Re-enable only when the user asks:
  `gh api -X PUT repos/bigbatmanorg/rss-publisher-agent/actions/permissions -F enabled=true`.
- **Sync rule:** any MCP change that the appliance depends on must be committed, pushed,
  tagged, and reflected in the agent repo's `RSS_PUBLISHER_MCP_REF` in the same session.
  Never leave the agent pinned to a ref that does not contain the fix it needs.
- Keep `STATUS.md` in both repos updated as you go (tests, failures, blockers, next action).

## State at handoff

### Already done (do not redo)

- Pinned `DOCKER_AGENT_VERSION=v1.144.0` with verified amd64 SHA-256.
  **The appliance is amd64-only** — multi-arch/arm64 support was explicitly dropped
  (session 2). The Dockerfile always installs the amd64 docker-agent binary; do not
  re-add arm64 work.
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

1. ~~MCP repo is private.~~ **RESOLVED.** The repo is now public and anonymously
   clonable (`git clone --branch v0.1.0 https://github.com/bigbatmanorg/rss-publisher-mcp.git`
   succeeds without credentials), so the Dockerfile's `git+https` install works.
2. ~~The `v0.1.0` tag predates the schema fix.~~ **RESOLVED.** The MCP schema fix was
   committed (`e20432a`), pushed to `main`, and `v0.1.0` was moved to that commit and
   force-pushed. Verified the tag contains `EntryPatch`/`_payload`; MCP `pytest` passes.
3. ~~Agent repo has no GitHub remote.~~ **RESOLVED.** `bigbatmanorg/rss-publisher-agent`
   is published (public), `origin` is configured, and local `master` is in sync with
   `origin/master`. GitHub Actions is disabled on this repo until local verification is
   complete.

### Behavior gates — improved but FLAKY (model non-determinism)

Session 2 hardened `agent.yaml` (explicit refuse-when-no-facts rule, verbatim
continuity_key handling, per-lifecycle tool mapping, publish_batch few-shot).
**Best run: 14/15 passing** — the fabricated-Nobel-Prize scenario now reliably passes,
and continuity_key / GUID preservation / publish_batch all passed in that run.

**Remaining problem: the `brain` model is non-deterministic.** A repeat run of the
identical suite regressed to 8/13 with different failures (mutated continuity key,
skipped entries, `update_entry` used for corrections). This is a model-consistency
limit, not a deterministic-core bug. **Next: try `AGENT_MODEL=brain-agent` (or
`brain-thinking`) and run the suite 2-3 times for consistency.** If still flaky,
document as an upstream model blocker with the reproducible suite.

## Remaining tasks

1. ~~Build the container locally for amd64 and arm64~~ **DONE (amd64-only).** amd64
   image builds locally and via the earlier CI run; arm64 requirement dropped.
2. **Stabilize the behavior scenarios** (see above): switch `AGENT_MODEL`, re-run
   `/tmp/appliance/scenarios.py` 2-3 times to a consistent 15/15.
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
11. Re-enable GitHub Actions on the agent repo only after local verification is complete.

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
