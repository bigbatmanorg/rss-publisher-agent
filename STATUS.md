# Status

Release-finishing pass in progress. This file is the authoritative handoff: it
records exactly what is done, what is broken, and where to continue.

Last updated: 2026-09-26 (session 1).

## Repositories

- **MCP**: `https://github.com/bigbatmanorg/rss-publisher-mcp` — public, branch `main`,
  tag `v0.1.0` (contains the typed-schema fix). CI enabled and passing.
- **Agent**: `https://github.com/bigbatmanorg/rss-publisher-agent` — public, branch
  `master`, `origin` configured, local and remote in sync at `a8d947e`.
  **GitHub Actions is DISABLED** for this repo (`actions/permissions` `enabled=false`)
  until everything works locally. Re-enable with:
  `gh api -X PUT repos/bigbatmanorg/rss-publisher-agent/actions/permissions -F enabled=true`.
- The one CI run that did execute (before disabling) passed in 37s, including the
  `linux/amd64` docker build against the public MCP repo — so the container build path
  is confirmed working on amd64.

## Environment (verified this session)

- Docker 29.8.1
- `docker-agent` **v1.144.0** installed at `/usr/local/bin/docker-agent`
  (`docker-agent version`; note `--version` is not a valid flag)
- Agent repo venv: Python 3.12.3 (`.venv`, created with `uv venv --python 3.12`)
- MCP repo venv: Python 3.14.7 (`/home/toor/projects/rss-publisher-mcp-v0.1.0/rss-publisher-mcp/.venv`)
- Model endpoint `http://pgx.home:4000/v1` (LiteLLM). Chat model `brain`.
  Embeddings model `embeddings` (native 2560 dims).
- `caddy` 2.11.4 and `supervisor` 4.3.0 installed locally for native integration runs
  (`~/.local/bin/caddy`, `~/.local/bin/supervisord`)

## Pins (done)

- `Dockerfile` / `docker-compose.yml`: `DOCKER_AGENT_VERSION=v1.144.0` with verified
  SHA-256 for amd64 and arm64 (both recomputed from the release assets this session).
- `RSS_PUBLISHER_MCP_REF=v0.1.0` (no longer `main`).
- Caddy image pinned `2.11.4`.

## Defects found and fixed

1. **`uv run pytest` was broken.** setuptools flat-layout auto-discovery failed on
   `specs/`, `static/`, `supervisor/`. Fixed with `[tool.setuptools] packages = []`
   in `pyproject.toml`. `uv run pytest` now passes (9 passed).
2. **supervisord orphaned the publisher MCP process.** `command=/bin/sh -lc '...'`
   made supervisord track the shell, not the server, so restarts left the real
   process holding `127.0.0.1:8766` and the program crash-looped with
   `[Errno 98] address already in use`. Fixed to a direct command plus
   `environment=RSS_MCP_TRANSPORT="streamable-http"`.
3. **Embeddings config was wrong.** `.env` had `RSS_EMBEDDINGS_MODEL=text-embeddings`
   (invalid model) and `RSS_EMBEDDINGS_DIMENSIONS=384` (wrong). The endpoint rejects
   the OpenAI `dimensions` parameter with HTTP 400, which silently degraded semantic
   search. Fixed to `RSS_EMBEDDINGS_MODEL=embeddings` and dimensions left unset.
4. **MCP tool schemas were opaque (fixed in the MCP repo).** `create_entry`/`update_entry`/
   `publish_batch`/`configure_feed`/`find_similar_active_entries` exposed `entry`/`patch`
   as `{"type":"object"}` with no properties, so the model invented field names
   (`presentation_html`) and every create failed validation. Fixed by typing the
   parameters with `FeedEntry`/`EntryPatch`/`BatchOperation`/`FeedConfig` and adding a
   `_payload()` coercion helper. See MCP repo changes below.
5. **Model does not emit tool calls when 16 tools are exposed.** With all 16 publisher
   tools the configured model returned a fabricated JSON summary as plain text and
   `tool_calls=0`. It works reliably at <=15 tools. Fixed by adding a `tools:` filter to
   the MCP toolset in `agent.yaml` exposing 14 tools. **The filter requires the
   `publisher_`-prefixed names**; unprefixed names match zero tools.
6. **Docker Agent version was stale.** Repo pinned v1.143.0 while the current release
   (and the installed binary) is v1.144.0. Re-pinned to v1.144.0.
7. **Agent instruction hardening.** Added a `TOOL CALLING RULES` block: never claim
   success without a tool result, omit `expected_revision` (inventing it caused
   revision-conflict retry loops), call each tool once, use only real FeedEntry fields.

## Verified working (native appliance, no container)

Ran the full appliance natively (supervisord + caddy + docker-agent) with local paths
because `/srv` and `/etc/caddy` are not writable without sudo. Harness lives in
`/tmp/appliance/` (`run.sh`, `supervisord.local.conf`, `gen_local_runtime.py`,
`scenarios.py`, `chat.sh`).

- All 7 supervised processes start and stay up; `/readyz` returns
  `{"status":"ready","checks":{...all true}}`.
- Public surface: `/healthz`, `/readyz`, `/feed.xml` (200, `application/rss+xml`),
  `/upload/` (200), `/.well-known/rss-publisher.json`, `/.well-known/agent-card.json`.
- **Publisher MCP is private:** `/publisher/mcp` -> 404; Caddyfile contains no
  `127.0.0.1:8766` route.
- **Docker Agent remote private MCP connection works:** debug log shows
  `Listed MCP tools count=16 server=127.0.0.1:8766` with `allow_private_ips: true`.
- `docker-agent run ./agent.yaml --dry-run` validates the config.
- `serve mcp`, `serve a2a`, `serve chat` all start on 8081/8082/8083.
- A2A Agent Card is served and loopback URLs are rewritten to the public `/a2a` base.
- Real publishing works end-to-end: sparse note -> `create_entry` -> entry in SQLite,
  `feed_revision` incremented, entry rendered into `feed.xml`.
- Agent answers the configured upload URL from env-injected instructions.

## Behavior scenarios (task 4/5) — 9/14 passing, NOT yet release-ready

Harness: `/tmp/appliance/scenarios.py` (run against a freshly reset appliance).

Passing: sparse note creates a readable entry; article creates an entry and preserves
supplied text; similar-but-unrelated creates a new GUID; ambiguous biases to create;
archive sets `archived`; republish revives; upload URL answered from env.

**Failing (must be fixed or documented as an upstream blocker):**

1. `status update uses continuity_key` — `found=0`. The agent did not set the supplied
   `continuity_key` on the status entry.
2. `active update preserves GUID` — depends on (1); no continuity key means no update.
3. `correction sets lifecycle=corrected` — lifecycle stayed `published`.
4. `batch uses publish_batch` — `batch_ops=0`; the agent created entries individually
   instead of using `publish_batch`.
5. **`does not invent sources/URLs` — FAILED and is the most serious.** Asked to publish
   a note about "the latest Nobel Prize winner" with a source URL, the agent **published a
   fabricated entry** ("2024 Nobel Prize...") with an invented ID instead of refusing or
   asking for the missing facts. This directly violates the editorial boundary and
   release gate "agent never invents missing facts/URLs/sources".

These failures are model-behavior (prompt/instruction) issues, not deterministic-core
bugs. The configured model (`brain`) is weak at multi-step tool orchestration and at
refusing underspecified input. Options to continue: strengthen the instruction further,
switch `AGENT_MODEL` to a stronger tool-calling model, or add a deterministic pre-check.

## Blockers

- ~~The MCP repo is private.~~ **RESOLVED.** `bigbatmanorg/rss-publisher-mcp` is now
  public and anonymously clonable, so the Dockerfile's `git+https` install works. The
  container build is no longer blocked by access (still needs to be run). Verified the
  exact Dockerfile install command succeeds and the tagged package contains the fix:
  `uv pip install "rss-publisher-mcp @ git+https://github.com/bigbatmanorg/rss-publisher-mcp.git@v0.1.0"`
  -> `installed 0.1.0 EntryPatch ok`.
- ~~The `v0.1.0` tag does not contain the schema fix.~~ **RESOLVED.** The MCP schema fix
  was committed (`e20432a`), pushed to `main`, and the `v0.1.0` tag was moved to that
  commit and force-pushed. Verified: `git show v0.1.0:src/rss_publisher/models.py`
  contains `EntryPatch` and `mcp_server.py` contains `_payload`; MCP `pytest` passes
  (152 passed, 1 skipped).
- ~~Agent repo has no GitHub remote.~~ **RESOLVED.** `bigbatmanorg/rss-publisher-agent`
  is published (public), `origin` is configured, and local `master` is in sync with
  `origin/master` at `a8d947e`. GitHub Actions is disabled (see Git workflow).

## Git workflow (authorized)

Commits and pushes are authorized in both repos; keep them in sync.

- MCP repo: `origin` = `https://github.com/bigbatmanorg/rss-publisher-mcp.git`, branch
  `main`. Commit, push, and move/cut the release tag when a change affects the appliance,
  then bump `RSS_PUBLISHER_MCP_REF` in the agent repo.
- Agent repo: `origin` = `https://github.com/bigbatmanorg/rss-publisher-agent.git`,
  branch `master`. Commit and push freely.
- **GitHub Actions is disabled on the agent repo** until local verification is complete.
  Do not re-enable it as part of routine work; the user will decide when.
- Any MCP change the appliance depends on must be committed, pushed, tagged, and
  reflected in `RSS_PUBLISHER_MCP_REF` in the same session.

## Not yet done

- Container build and multi-arch validation (task 12) — amd64 confirmed via the one CI
  run; arm64 still to be validated locally.
- `RSS_AUTH_MODE=bearer` end-to-end through Caddy (task 7).
- Uploads from `/upload/` and direct HTTP API (task 8).
- `/agent/mcp`, A2A and `/v1/chat/completions` behavior parity (task 10).
- Embeddings on/off verification (task 14).
- URL-injection coherence test (task 6) — partially observed, not formally asserted.
- Release-gate checkboxes in `specs/RELEASE_GATES.md` not yet ticked.

## Exact next action

1. Run `docker build` locally for amd64 and arm64 (access blocker resolved).
2. Fix the 5 failing behavior scenarios (start with the fabricated-Nobel entry).
3. Then run the remaining gates: bearer mode, uploads, protocol parity, embeddings on/off.
4. Re-enable GitHub Actions only after local verification is complete.
