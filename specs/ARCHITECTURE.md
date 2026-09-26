# RSS Publisher Agent appliance architecture

Repository target: `https://github.com/bigbatmanorg/rss-publisher-agent`

## Product boundary

The agent is a light editorial publisher, not a research agent. It receives already-curated information, may generate presentation metadata from that information, resolves whether an active entry should be updated, and calls the private deterministic `rss-publisher-mcp` backend.

`rss-publisher-mcp` is a dependency and does not know this agent exists.

## Public surface

One Caddy port exposes:

- `/` publication home
- `/feed.xml`
- `/entries/*`
- `/media/*`
- `/files/*`
- `/upload/`
- `/api/v1/assets` and asset metadata/service discovery
- `/agent/mcp` — intelligent RSS Publisher Agent as MCP
- `/a2a` and `/.well-known/agent-card.json` — Docker Agent A2A adapter
- `/v1/models` and `/v1/chat/completions` — OpenAI-compatible adapter
- `/.well-known/rss-publisher.json`
- `/healthz`, `/readyz`

There is **no public deterministic Publisher MCP endpoint**.

## Internal topology

- Publisher HTTP API: `127.0.0.1:8765`
- Private Publisher MCP: `127.0.0.1:8766/mcp`
- Agent MCP adapter: `127.0.0.1:8081`
- Agent A2A adapter: `127.0.0.1:8082`
- Agent OpenAI Chat adapter: `127.0.0.1:8083`
- Appliance readiness helper: `127.0.0.1:8090`
- Caddy: public `:8080`

All child processes are supervised. Only Caddy is exposed.

## Authentication

`RSS_AUTH_MODE=none` is valid for trusted labs. `RSS_AUTH_MODE=bearer` protects intelligent agent interfaces at Caddy and the upload API at the publisher backend. Read-only publication content and discovery remain public.

No secret is ever emitted in discovery metadata.
