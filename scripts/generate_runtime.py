from __future__ import annotations

import json
import os
from pathlib import Path


def endpoints(env=os.environ):
    base = env.get("RSS_PUBLIC_BASE_URL", "http://localhost:8080").rstrip("/")
    return {
        "base_url": base,
        "feed_url": base + env.get("RSS_FEED_PATH", "/feed.xml"),
        "upload_page": base + "/upload/",
        "upload_url": base + "/api/v1/assets",
        "agent_mcp_url": base + "/agent/mcp",
        "a2a_url": base + "/a2a",
        "a2a_agent_card": base + "/.well-known/agent-card.json",
        "openai_base_url": base + "/v1",
        "media_base_url": base + env.get("RSS_MEDIA_PATH", "/media") + "/",
        "files_base_url": base + env.get("RSS_FILES_PATH", "/files") + "/",
    }


def manifest(env=os.environ):
    ep = endpoints(env)
    return {
        "name": "RSS Publisher Agent",
        "version": "0.1.0",
        "publication": {
            "base_url": ep["base_url"], "feed_url": ep["feed_url"],
            "media_url": ep["media_base_url"], "files_url": ep["files_base_url"],
        },
        "uploads": {
            "page": ep["upload_page"], "url": ep["upload_url"],
            "method": "POST", "content_type": "multipart/form-data",
            "max_size_bytes": int(env.get("RSS_MAX_UPLOAD_BYTES", "104857600")),
            "authentication": env.get("RSS_AUTH_MODE", "none"),
        },
        "agent": {
            "mcp_url": ep["agent_mcp_url"],
            "a2a_url": ep["a2a_url"],
            "agent_card": ep["a2a_agent_card"],
            "openai_base_url": ep["openai_base_url"],
            "authentication": env.get("RSS_AUTH_MODE", "none"),
        },
        "notes": [
            "The deterministic RSS Publisher MCP is private inside the appliance and is not exposed publicly.",
            "Upload binary assets over HTTP first, then pass the returned asset_id to the publishing agent.",
        ],
    }


def caddyfile(env=os.environ) -> str:
    site = env.get("RSS_CADDY_SITE", ":8080")
    auth_mode = env.get("RSS_AUTH_MODE", "none").lower()
    token = env.get("RSS_API_TOKEN", "")
    max_bytes = env.get("RSS_MAX_UPLOAD_BYTES", "104857600")
    auth = ""
    if auth_mode == "bearer":
        if not token:
            raise RuntimeError("RSS_API_TOKEN is required when RSS_AUTH_MODE=bearer")
        safe = token.replace('"', '\\"')
        auth = f'''\n    @unauthorized {{\n        path /agent/* /a2a /a2a/* /v1/*\n        not header Authorization "Bearer {safe}"\n    }}\n    respond @unauthorized "Unauthorized" 401\n'''
    return f'''{site} {{
    encode zstd gzip
    request_body /api/v1/assets {{
        max_size {max_bytes}
    }}
{auth}
    handle /healthz {{
        reverse_proxy 127.0.0.1:8090
    }}
    handle /readyz {{
        reverse_proxy 127.0.0.1:8090
    }}
    handle /.well-known/rss-publisher.json {{
        reverse_proxy 127.0.0.1:8090
    }}
    handle /.well-known/agent-card.json {{
        reverse_proxy 127.0.0.1:8090
    }}
    handle /api/* {{
        reverse_proxy 127.0.0.1:8765
    }}
    handle_path /agent/* {{
        reverse_proxy 127.0.0.1:8081
    }}
    handle /a2a* {{
        uri strip_prefix /a2a
        reverse_proxy 127.0.0.1:8082
    }}
    handle /v1/* {{
        reverse_proxy 127.0.0.1:8083
    }}
    handle {{
        root * /srv/public
        @feed path /feed.xml
        header @feed Content-Type "application/rss+xml; charset=utf-8"
        header @feed Cache-Control "no-cache"
        @immutable path /media/* /files/*
        header @immutable Cache-Control "public, max-age=31536000, immutable"
        @files path /files/*
        header @files Content-Disposition "attachment"
        header X-Content-Type-Options "nosniff"
        file_server
    }}
}}
'''


def main():
    Path("/etc/caddy").mkdir(parents=True, exist_ok=True)
    Path("/etc/caddy/Caddyfile").write_text(caddyfile())
    Path("/srv/public").mkdir(parents=True, exist_ok=True)
    well = Path("/srv/public/.well-known")
    well.mkdir(parents=True, exist_ok=True)
    well.joinpath("rss-publisher.json").write_text(json.dumps(manifest(), indent=2))


if __name__ == "__main__":
    main()
