# syntax=docker/dockerfile:1.7
ARG CADDY_VERSION=2.11.4
FROM caddy:${CADDY_VERSION} AS caddy

FROM python:3.12-slim
ARG TARGETARCH
ARG DOCKER_AGENT_VERSION=v1.144.0
ARG DOCKER_AGENT_SHA256_AMD64=2bb722260a28ed5a6d0773691fac1952f055b0c0889ff2af615a2fcd44ffba14
ARG DOCKER_AGENT_SHA256_ARM64=3ec28ff2dd1054613a21d08e22497af058d98c12dfd023a3b8a38044c22bf1fc
ARG RSS_PUBLISHER_MCP_REF=v0.1.0

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv supervisor fastapi uvicorn httpx
COPY --from=caddy /usr/bin/caddy /usr/bin/caddy

RUN set -eux; \
    case "${TARGETARCH:-amd64}" in \
      amd64) DA_ARCH=amd64; DA_SHA256="${DOCKER_AGENT_SHA256_AMD64}" ;; \
      arm64) DA_ARCH=arm64; DA_SHA256="${DOCKER_AGENT_SHA256_ARM64}" ;; \
      *) echo "unsupported TARGETARCH=${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    curl -fsSL "https://github.com/docker/docker-agent/releases/download/${DOCKER_AGENT_VERSION}/docker-agent-linux-${DA_ARCH}" -o /usr/local/bin/docker-agent; \
    echo "${DA_SHA256}  /usr/local/bin/docker-agent" | sha256sum -c -; \
    chmod +x /usr/local/bin/docker-agent; \
    /usr/local/bin/docker-agent version

RUN uv pip install --system "rss-publisher-mcp @ git+https://github.com/bigbatmanorg/rss-publisher-mcp.git@${RSS_PUBLISHER_MCP_REF}"

WORKDIR /app
COPY . /app
RUN mkdir -p /data /srv/public /etc/caddy /var/log/supervisor

EXPOSE 8080
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD curl -fsS http://127.0.0.1:8080/readyz >/dev/null || exit 1
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
