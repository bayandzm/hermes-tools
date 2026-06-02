#!/usr/bin/env python3
"""
Hermes Tools API — REST + MCP endpoint
Run: python3 api_server.py --port 8765
"""
import json, os, sys
import urllib.request as ur
from datetime import datetime, timezone
from pathlib import Path

# Check if FastAPI is available
try:
    from fastapi import FastAPI, Query
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
except ImportError:
    print("Need FastAPI + uvicorn. Run: pip3 install fastapi uvicorn --break-system-packages")
    sys.exit(1)

app = FastAPI(title="Hermes Tools API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

OUTPUT_DIR = Path.home() / "crypto-content-bot" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── API ROUTES ────────────────────────────────────

@app.get("/")
def root():
    return {"name": "Hermes Tools API", "version": "1.0", "endpoints": [
        "/api/btc", "/api/fear-greed", "/api/dominance", "/api/summary",
        "/api/polymarket", "/api/generate"
    ]}

@app.get("/api/btc")
def btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true"
    req = ur.Request(url, headers={"User-Agent": "HermesAPI/1.0"})
    with ur.urlopen(req, timeout=15) as r:
        btc = json.loads(r.read())["bitcoin"]
    return {"price_usd": btc["usd"], "24h_change_pct": btc["usd_24h_change"],
            "market_cap": btc["usd_market_cap"], "volume_24h": btc["usd_24h_vol"],
            "ts": datetime.now(timezone.utc).isoformat()}

@app.get("/api/fear-greed")
def fear_greed():
    req = ur.Request("https://api.alternative.me/fng/?limit=1", headers={"User-Agent": "HermesAPI/1.0"})
    with ur.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())["data"][0]
    return {"value": int(data["value"]), "classification": data["value_classification"]}

@app.get("/api/dominance")
def dominance():
    req = ur.Request("https://api.coingecko.com/api/v3/global", headers={"User-Agent": "HermesAPI/1.0"})
    with ur.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    return {"btc_dominance": data["data"]["market_cap_percentage"]["btc"]}

@app.get("/api/summary")
def summary():
    hdr = {"User-Agent": "HermesAPI/1.0"}
    btc_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
    req1 = ur.Request(btc_url, headers=hdr)
    with ur.urlopen(req1, timeout=10) as r:
        btc = json.loads(r.read())["bitcoin"]
    req2 = ur.Request("https://api.alternative.me/fng/?limit=1", headers=hdr)
    with ur.urlopen(req2, timeout=10) as r:
        fg = json.loads(r.read())["data"][0]
    req3 = ur.Request("https://api.coingecko.com/api/v3/global", headers=hdr)
    with ur.urlopen(req3, timeout=10) as r:
        dom = json.loads(r.read())
    return {
        "btc_price": btc["usd"], "btc_24h_change": btc["usd_24h_change"],
        "fear_greed": int(fg["value"]), "fear_greed_label": fg["value_classification"],
        "btc_dominance": dom["data"]["market_cap_percentage"]["btc"],
        "ts": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/polymarket")
def polymarket(limit: int = 5):
    try:
        url = f"https://gamma-api.polymarket.com/markets?limit={limit}&order=volume24h&ascending=false"
        req = ur.Request(url, headers={"User-Agent": "HermesAPI/1.0"})
        with ur.urlopen(req, timeout=15) as r:
            markets = json.loads(r.read())
        return {"markets": [{"question": m.get("question"), "volume_24h": m.get("volume24hr"),
                "outcomes": m.get("outcomePrices")} for m in markets[:limit]]}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/generate")
def generate_image(prompt: str = Query(...), token: str = Query(None)):
    """Generate AI image via Flux Schnell"""
    hf_token = token or os.environ.get("HF_TOKEN", "")
    if not hf_token:
        return {"error": "HF_TOKEN required (pass as ?token= or set env)", "status": "unauthorized"}

    try:
        payload = json.dumps({"inputs": prompt}).encode()
        req = ur.Request(
            "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
            data=payload,
            headers={"Authorization": f"Bearer {hf_token}", "Content-Type": "application/json"}
        )
        with ur.urlopen(req, timeout=90) as r:
            data = r.read()
        filename = f"flux_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = OUTPUT_DIR / filename
        filepath.write_bytes(data)
        return {"status": "success", "file": str(filepath), "size_bytes": len(data)}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
