import importlib.util
from pathlib import Path

MODULE = Path(__file__).parents[1] / "scripts" / "generate_runtime.py"
spec = importlib.util.spec_from_file_location("generate_runtime", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_manifest_derives_every_url_from_base():
    env = {
        "RSS_PUBLIC_BASE_URL": "https://rss.lab.amvc.me",
        "RSS_AUTH_MODE": "none",
        "RSS_FEED_PATH": "/feed.xml",
        "RSS_MEDIA_PATH": "/media",
        "RSS_FILES_PATH": "/files",
    }
    m = mod.manifest(env)
    assert m["publication"]["feed_url"] == "https://rss.lab.amvc.me/feed.xml"
    assert m["uploads"]["url"] == "https://rss.lab.amvc.me/api/v1/assets"
    assert m["agent"]["mcp_url"] == "https://rss.lab.amvc.me/agent/mcp"
    assert "publisher/mcp" not in str(m)


def test_caddy_has_no_public_publisher_mcp():
    caddy = mod.caddyfile({"RSS_CADDY_SITE": ":8080", "RSS_AUTH_MODE": "none", "RSS_MAX_UPLOAD_BYTES": "100000"})
    assert "/agent/" in caddy
    assert "/api/*" in caddy
    assert "/publisher/mcp" not in caddy
    assert "127.0.0.1:8766" not in caddy
    # Public A2A card is rewritten by the runtime helper so it advertises /a2a, not loopback URLs.
    assert "handle /.well-known/agent-card.json" in caddy
    card_block = caddy.split("handle /.well-known/agent-card.json", 1)[1].split("}", 1)[0]
    assert "127.0.0.1:8090" in card_block


def test_bearer_mode_generates_edge_guard():
    caddy = mod.caddyfile({"RSS_CADDY_SITE": ":8080", "RSS_AUTH_MODE": "bearer", "RSS_API_TOKEN": "secret", "RSS_MAX_UPLOAD_BYTES": "100000"})
    assert 'not header Authorization "Bearer secret"' in caddy
    assert "Unauthorized" in caddy
