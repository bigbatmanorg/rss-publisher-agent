import importlib.util
import sys
from pathlib import Path

MODULE = Path(__file__).parents[1] / "scripts" / "appliance_runtime.py"
sys.path.insert(0, str(MODULE.parent))
spec = importlib.util.spec_from_file_location("appliance_runtime", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_rewrite_a2a_card_preserves_shape_and_rewrites_loopback_urls():
    card = {
        "name": "RSS Publisher Agent",
        "supportedInterfaces": [
            {"url": "http://127.0.0.1:8082/invoke", "protocolBinding": "JSONRPC"},
            {"url": "http://localhost:8082/other", "protocolBinding": "HTTP+JSON"},
        ],
        "skills": [{"id": "publish", "description": "publish"}],
    }
    result = mod.rewrite_agent_card_urls(card, "http://127.0.0.1:8082", "https://rss.amvc.me/a2a")
    assert result["supportedInterfaces"][0]["url"] == "https://rss.amvc.me/a2a/invoke"
    assert result["supportedInterfaces"][1]["url"] == "https://rss.amvc.me/a2a/other"
    assert result["skills"] == card["skills"]


def test_manifest_declares_agent_auth_mode():
    m = mod.manifest({"RSS_PUBLIC_BASE_URL": "https://rss.amvc.me", "RSS_AUTH_MODE": "bearer"})
    assert m["agent"]["authentication"] == "bearer"
