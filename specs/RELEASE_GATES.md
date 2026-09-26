# Release gates

## Agent behavior

- [x] Docker Agent config validates with the pinned Docker Agent version
- [x] One-shot sparse status input becomes a readable entry without external research
- [x] Rich prewritten content is preserved rather than unnecessarily rewritten
- [x] Existing active semantic match is updated with same GUID
- [x] unrelated but similar topic creates a new GUID
- [x] ambiguous match biases to create, not false merge
- [x] exact continuity_key updates existing active entry
- [x] archived target is not silently revived
- [x] correction/retraction/unpublish instructions select correct MCP operations
- [x] batch input uses batch publishing
- [x] agent can answer the runtime upload URL from environment-injected instructions
- [x] agent never attempts to call a public `/publisher/mcp`

## Protocol/deployment

- [x] external `/agent/mcp` works
- [x] external A2A works with the Docker Agent version actually bundled; advertised A2A version is truthful
- [x] `/v1/models` and `/v1/chat/completions` work
- [x] ACP local/stdin invocation documented and smoke-tested outside Caddy
- [x] upload UI uploads through the same `/api/v1/assets` endpoint as machines
- [x] `.well-known/rss-publisher.json` contains runtime-derived URLs and no secret
- [x] `RSS_AUTH_MODE=none` works in a trusted lab
- [x] bearer mode rejects unauthenticated write/agent requests
- [x] public RSS/media/pages remain anonymous in bearer mode
- [x] only one Docker port is exposed
- [x] child process failure is restarted or makes readiness fail
- [x] SIGTERM shuts the appliance down cleanly
- [x] image builds for amd64 (arm64/multi-arch support intentionally dropped; amd64-only appliance)

## Dependency risk

Docker Agent A2A is currently marked early/evolving. Compatibility must be tested against the exact pinned Docker Agent release instead of assuming a particular A2A spec revision.
