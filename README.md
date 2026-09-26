# rss-publisher-agent

One-shot generic RSS publishing agent and self-contained Docker appliance.

Repository target: `https://github.com/bigbatmanorg/rss-publisher-agent`

Dependency: `https://github.com/bigbatmanorg/rss-publisher-mcp`

## What it does

The agent receives already-curated information. It may generate a title, summary, categories, presentation HTML, `kind`, and continuity key from the supplied information, but it does not browse/research/fact-check externally. Before implicitly creating an entry it checks currently active feed entries and decides whether the information continues one of them.

It is usable as:

- a Docker Agent/sub-agent definition
- an intelligent MCP endpoint
- an A2A agent
- an OpenAI-compatible Chat endpoint
- a normal one-container RSS publication appliance

The deterministic publisher MCP stays private inside the appliance.

## Quick start after both GitHub repos exist

```bash
cp .env.example .env
# edit RSS_PUBLIC_BASE_URL and AGENT_* model values
docker compose up --build -d
```

Open:

```text
http://localhost:8080/
http://localhost:8080/feed.xml
http://localhost:8080/upload/
http://localhost:8080/.well-known/rss-publisher.json
```

For a public reverse proxy set, for example:

```env
RSS_PUBLIC_BASE_URL=https://rss.amvc.me
```

For lab:

```env
RSS_PUBLIC_BASE_URL=https://rss.lab.amvc.me
RSS_AUTH_MODE=none
```

## Public protocol endpoints

```text
/agent/mcp                  intelligent agent exposed as MCP
/a2a                        intelligent agent exposed as A2A
/v1/models                  OpenAI-compatible model discovery
/v1/chat/completions        OpenAI-compatible invocation
```

Binary media should be uploaded first:

```text
POST /api/v1/assets
```

The response returns an `asset_id`. Give that ID to the publishing agent with the information to publish.

There is deliberately **no** public `/publisher/mcp` route.

## ACP (local/stdin)

In addition to the networked adapters above, the same agent can be invoked over the
Agent Client Protocol (ACP) on stdin/stdout, outside Caddy, with the bundled Docker
Agent:

```bash
docker-agent serve acp ./agent.yaml
```

ACP speaks newline-delimited JSON-RPC over stdio. A minimal handshake:

```jsonc
// -> initialize
{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":1,"clientCapabilities":{}}}
// <- result includes agentInfo (name/version) and agentCapabilities
// -> session/new
{"jsonrpc":"2.0","id":1,"method":"session/new","params":{"cwd":".","mcpServers":[]}}
// <- result includes sessionId (async session/update notifications may arrive first)
// -> session/prompt
{"jsonrpc":"2.0","id":2,"method":"session/prompt","params":{"sessionId":"<id>","prompt":[{"type":"text","text":"Publish this note: ..."}]}}
```

Keep stdin open for the lifetime of the session; closing stdin stops the agent. ACP is
a local invocation path and is not routed through Caddy.

## Authentication

Lab:

```env
RSS_AUTH_MODE=none
```

Internet-facing:

```env
RSS_AUTH_MODE=bearer
RSS_API_TOKEN=long-random-value
```

The publication itself remains publicly readable. Bearer mode protects uploads and agent invocation interfaces.

## Development tests

```bash
uv sync --extra dev
uv run pytest
```

These tests check URL derivation, absence of public Publisher MCP routing, auth Caddy generation, the agent's single private toolset, behavioral instruction invariants, and upload UI wiring.

## Important dependency note

Docker Agent A2A support is currently evolving. The bundled Docker Agent release must be integration-tested before release; the appliance should not claim a protocol version merely because the upstream A2A specification has one.
