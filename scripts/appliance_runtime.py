from __future__ import annotations

import os
import socket
import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from generate_runtime import manifest, endpoints

app = FastAPI(title="RSS Publisher Appliance Runtime")


def rewrite_agent_card_urls(value, internal_base: str, public_a2a_base: str):
    """Rewrite Docker Agent loopback A2A URLs for the externally routed /a2a prefix.

    Docker Agent owns the actual Agent Card schema/version. This helper intentionally
    preserves that payload and changes URL strings only, so we do not fork the evolving
    A2A schema in this appliance.
    """
    if isinstance(value, dict):
        return {k: rewrite_agent_card_urls(v, internal_base, public_a2a_base) for k, v in value.items()}
    if isinstance(value, list):
        return [rewrite_agent_card_urls(v, internal_base, public_a2a_base) for v in value]
    if isinstance(value, str):
        for prefix in (internal_base, internal_base.replace("127.0.0.1", "localhost")):
            if value.startswith(prefix):
                suffix = value[len(prefix):]
                return public_a2a_base.rstrip("/") + (suffix if suffix.startswith("/") else "/" + suffix if suffix else "")
    return value


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


def port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.4):
            return True
    except OSError:
        return False


@app.get("/readyz")
def readyz():
    checks = {}
    try:
        r = httpx.get("http://127.0.0.1:8765/healthz", timeout=1)
        checks["publisher_api"] = r.status_code == 200
    except Exception:
        checks["publisher_api"] = False
    checks["publisher_mcp"] = port_open(8766)
    checks["agent_mcp"] = port_open(8081)
    checks["agent_a2a"] = port_open(8082)
    checks["agent_chat"] = port_open(8083)
    ok = all(checks.values())
    payload = {"status": "ready" if ok else "not_ready", "checks": checks}
    return payload if ok else JSONResponse(status_code=503, content=payload)


@app.get("/.well-known/rss-publisher.json")
def publisher_manifest():
    return manifest()


@app.get("/.well-known/agent-card.json")
def public_agent_card():
    try:
        response = httpx.get("http://127.0.0.1:8082/.well-known/agent-card.json", timeout=2)
        response.raise_for_status()
        payload = response.json()
        public_a2a = endpoints()["a2a_url"]
        return rewrite_agent_card_urls(payload, "http://127.0.0.1:8082", public_a2a)
    except Exception as exc:
        return JSONResponse(status_code=503, content={"error": "a2a_agent_card_unavailable", "detail": str(exc)})


def main():
    uvicorn.run(app, host="127.0.0.1", port=8090, log_level=os.getenv("RSS_LOG_LEVEL", "info").lower())


if __name__ == "__main__":
    main()
