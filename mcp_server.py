#!/usr/bin/env python3
"""
MCP Server: Hermes Tools — crypto, Polymarket, image gen.
Usage: python3 mcp_server.py
Register in Hermes config.yaml under mcp_servers.
"""
import json, os, sys
import urllib.request as ur
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hermes-tools")
OUTPUT_DIR = Path.home() / "crypto-content-bot" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── TOOLS ──────────────────────────────────────────

@mcp.tool()
async def crypto_btc_price() -> str:
    """Current Bitcoin price, 24h change, market cap. Real-time from CoinGecko."""
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true"
    req = ur.Request(url, headers={"User-Agent": "MCP-Hermes/1.0"})
    with ur.urlopen(req, timeout=15) as r:
        btc = json.loads(r.read())["bitcoin"]
    return json.dumps({
        "price_usd": btc["usd"], "24h_change_pct": btc["usd_24h_change"],
        "market_cap": btc["usd_market_cap"], "volume_24h": btc["usd_24h_vol"],
        "ts": datetime.now(timezone.utc).isoformat()
    })

@mcp.tool()
async def crypto_fear_greed() -> str:
    """Fear & Greed Index (0-100)."""
    req = ur.Request("https://api.alternative.me/fng/?limit=1", headers={"User-Agent": "MCP/1.0"})
    with ur.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())["data"][0]
    return json.dumps({"value": int(data["value"]), "classification": data["value_classification"]})

@mcp.tool()
async def crypto_btc_dominance() -> str:
    """Bitcoin market dominance %."""
    req = ur.Request("https://api.coingecko.com/api/v3/global", headers={"User-Agent": "MCP/1.0"})
    with ur.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    return json.dumps({"btc_dominance": data["data"]["market_cap_percentage"]["btc"]})

@mcp.tool()
async def crypto_market_summary() -> str:
    """Full market: BTC price + Fear & Greed + Dominance in one call."""
    btc_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
    hdr = {"User-Agent": "MCP/1.0"}
    req1 = ur.Request(btc_url, headers=hdr)
    with ur.urlopen(req1, timeout=10) as r:
        btc = json.loads(r.read())["bitcoin"]
    req2 = ur.Request("https://api.alternative.me/fng/?limit=1", headers=hdr)
    with ur.urlopen(req2, timeout=10) as r:
        fg = json.loads(r.read())["data"][0]
    req3 = ur.Request("https://api.coingecko.com/api/v3/global", headers=hdr)
    with ur.urlopen(req3, timeout=10) as r:
        dom = json.loads(r.read())
    return json.dumps({
        "btc_price": btc["usd"], "btc_24h_change": btc["usd_24h_change"],
        "fear_greed": int(fg["value"]), "fear_greed_label": fg["value_classification"],
        "btc_dominance": dom["data"]["market_cap_percentage"]["btc"],
        "ts": datetime.now(timezone.utc).isoformat()
    })

@mcp.tool()
async def polymarket_markets(limit: int = 5) -> str:
    """List top Polymarket markets by volume."""
    try:
        url = f"https://gamma-api.polymarket.com/markets?limit={limit}&order=volume24h&ascending=false"
        req = ur.Request(url, headers={"User-Agent": "MCP/1.0"})
        with ur.urlopen(req, timeout=15) as r:
            markets = json.loads(r.read())
        return json.dumps([{
            "question": m.get("question"), "volume_24h": m.get("volume24hr"),
            "outcomes": m.get("outcomePrices")
        } for m in markets[:limit]])
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
async def image_generate(prompt: str) -> str:
    """Generate image via Flux Schnell (free HF inference). Needs HF_TOKEN env."""
    try:
        token = os.environ.get("HF_TOKEN", os.environ.get("HUGGINGFACE_TOKEN", ""))
        if not token:
            return json.dumps({"error": "HF_TOKEN not set in environment"})
        payload = json.dumps({"inputs": prompt}).encode()
        req = ur.Request(
            "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
            data=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )
        with ur.urlopen(req, timeout=90) as r:
            data = r.read()
        filename = f"flux_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = OUTPUT_DIR / filename
        filepath.write_bytes(data)
        return json.dumps({"status": "success", "file": str(filepath), "size_bytes": len(data)})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─── RUN ─────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
