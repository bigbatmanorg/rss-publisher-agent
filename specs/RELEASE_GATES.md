# Release gates

## Agent behavior

- [ ] Docker Agent config validates with the pinned Docker Agent version
- [ ] One-shot sparse status input becomes a readable entry without external research
- [ ] Rich prewritten content is preserved rather than unnecessarily rewritten
- [ ] Existing active semantic match is updated with same GUID
- [ ] unrelated but similar topic creates a new GUID
- [ ] ambiguous match biases to create, not false merge
- [ ] exact continuity_key updates existing active entry
- [ ] archived target is not silently revived
- [ ] correction/retraction/unpublish instructions select correct MCP operations
- [ ] batch input uses batch publishing
- [ ] agent can answer the runtime upload URL from environment-injected instructions
- [ ] agent never attempts to call a public `/publisher/mcp`

## Protocol/deployment

- [ ] external `/agent/mcp` works
- [ ] external A2A works with the Docker Agent version actually bundled; advertised A2A version is truthful
- [ ] `/v1/models` and `/v1/chat/completions` work
- [ ] ACP local/stdin invocation documented and smoke-tested outside Caddy
- [ ] upload UI uploads through the same `/api/v1/assets` endpoint as machines
- [ ] `.well-known/rss-publisher.json` contains runtime-derived URLs and no secret
- [ ] `RSS_AUTH_MODE=none` works in a trusted lab
- [ ] bearer mode rejects unauthenticated write/agent requests
- [ ] public RSS/media/pages remain anonymous in bearer mode
- [ ] only one Docker port is exposed
- [ ] child process failure is restarted or makes readiness fail
- [ ] SIGTERM shuts the appliance down cleanly
- [ ] image builds for amd64 (arm64/multi-arch support intentionally dropped; amd64-only appliance)

## Dependency risk

Docker Agent A2A is currently marked early/evolving. Compatibility must be tested against the exact pinned Docker Agent release instead of assuming a particular A2A spec revision.
