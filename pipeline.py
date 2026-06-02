#!/usr/bin/env python3
"""Crypto Content Engine — Full Autonomous Pipeline"""
import json, sys, os, subprocess, base64
import urllib.request as ur
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "crypto-content-bot"
OUT = BASE / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

def fetch(url, timeout=15):
    try:
        req = ur.Request(url, headers={"User-Agent": "CryptoBot/1.0"})
        with ur.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except: return {}

# ─── 1. SCRAPE ────────────────────────────────────────
def scrape():
    btc = fetch("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true")
    fg = fetch("https://api.alternative.me/fng/?limit=1")
    total = fetch("https://api.coingecko.com/api/v3/global")

    return {
        "ts": datetime.utcnow().isoformat(),
        "price_usd": btc.get("bitcoin", {}).get("usd"),
        "change_24h": btc.get("bitcoin", {}).get("usd_24h_change"),
        "fear_greed": int(fg.get("data", [{}])[0].get("value", 50)),
        "fear_greed_label": fg.get("data", [{}])[0].get("value_classification", "N"),
        "dominance": total.get("data", {}).get("market_cap_percentage", {}).get("btc"),
    }

# ─── 2. AI ANALYST (StepFun free API) ─────────────────
HF_TOKEN = os.environ.get("HF_INFERENCE_TOKEN", "")
STEPFUN_KEY = os.environ.get("STEPFUN_API_KEY", os.environ.get("STEPFUN_KEY", ""))
OPENCODE_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")

def analyze(data):
    prompt = f"""You are a crypto analyst. Write ONE viral tweet about Bitcoin based on this data.
BTC: ${data.get('price_usd'):,.0f} | 24h: {data.get('change_24h'):+.1f}% | FearGreed: {data.get('fear_greed')}/100 ({data.get('fear_greed_label')}) | Dominance: {data.get('dominance'):.1f}%

Rules:
- Max 260 chars
- Use game theory lens (Saylor accumulation, ETF flows, miner capitulation cycle)
- Include 1 emoji
- No hashtags except $BTC
- Tone: analytical, not shilling
- Bahasa Indonesia campur English OK"""
    
    try:
        r = subprocess.run(["python3", "-c", f"""
import urllib.request as ur, json
body = json.dumps({{
    "model": "step-3.6",
    "messages": [{{"role": "user", "content": {json.dumps(prompt)}}}],
    "max_tokens": 300
}}).encode()
req = ur.Request("https://api.stepfun.ai/v1/chat/completions", data=body, headers={{
    "Authorization": "Bearer {STEPFUN_KEY}",
    "Content-Type": "application/json"
}})
with ur.urlopen(req) as r: print(json.loads(r.read())["choices"][0]["message"]["content"])
"""], capture_output=True, text=True, timeout=60)
        if r.returncode == 0: return r.stdout.strip()
    except: pass
    
    # Fallback: use OpenCode if StepFun unavailable
    try:
        r = subprocess.run(["python3", "-c", f"""
import urllib.request as ur, json
body = json.dumps({{
    "model": "deepseek-v4-flash",
    "messages": [{{"role": "user", "content": {json.dumps(prompt)}}}],
}}).encode()
req = ur.Request("https://opencode.ai/zen/go/v1/chat/completions", data=body, headers={{
    "Authorization": "Bearer {OPENCODE_KEY}",
    "Content-Type": "application/json"
}})
with ur.urlopen(req) as r: print(json.loads(r.read())["choices"][0]["message"]["content"])
"""], capture_output=True, text=True, timeout=60)
        if r.returncode == 0: return r.stdout.strip()
    except: pass
    
    return _manual_tweet(data)

def _manual_tweet(d):
    """Fallback manual tweet"""
    p = d['price_usd']
    c = d['change_24h']
    fg = d['fear_greed']
    direction = "bullish continuation" if c > 0 else "narrative reset"
    if fg < 25: mood = "extreme fear — historically best DCA zone"
    elif fg < 50: mood = "fear — accumulation phase"
    elif fg < 75: mood = "greed — distribution warning"
    else: mood = "extreme greed — caution"
    return f"BTC ${p:,.0f} | {c:+.1f}% 24h | {mood}\nGame theory: setiap cycle bottom = higher low. $BTC dominance tetap kontrol penuh."

# ─── 3. MEME GENERATOR (Flux HF) ──────────────────────
def generate_meme(tweet, data):
    prompt = f"""Crypto meme graphic, dark theme. Single image. 
Bitcoin rocket or game theory chessboard vibe.
Text overlay (max 2 lines): "{tweet[:100]}"
Clean design, no clutter. Meme coin style."""
    
    try:
        r = subprocess.run(["python3", "-c", f"""
import urllib.request as ur, json, base64
payload = json.dumps({{"inputs": {json.dumps(prompt)}, "model": "black-forest-labs/FLUX.1-schnell"}}).encode()
req = ur.Request("https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
    data=payload, headers={{"Authorization": "Bearer {HF_TOKEN}", "Content-Type": "application/json"}})
try:
    with ur.urlopen(req, timeout=90) as r:
        data = r.read()
except Exception as e:
    # Retry with Flux Pro
    payload2 = json.dumps({{"inputs": {json.dumps(prompt)}}}).encode()
    req2 = ur.Request("https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev",
        data=payload2, headers={{"Authorization": "Bearer {HF_TOKEN}"}})
    with ur.urlopen(req2, timeout=90) as r2:
        data = r2.read()
with open("{OUT}/meme.png", "wb") as f:
    f.write(data)
print("OK")
"""], capture_output=True, timeout=120)
        return r.returncode == 0 and b"OK" in r.stdout
    except: return False

# ─── 4. PUBLISH TO X ──────────────────────────────────
def publish(tweet, image_path=None):
    try:
        r = subprocess.run(["xurl", "post", tweet], capture_output=True, text=True, timeout=30)
        result = r.returncode == 0
        if result:
            print(f"  ✅ Posted to X: {tweet[:80]}...")
        else:
            print(f"  ❌ X post failed: {r.stderr[:100]}")
        return result
    except FileNotFoundError:
        print("  ⚠️ xurl not found — tweet logged only")
        return False

# ─── 5. SAVE LOG ─────────────────────────────────────
def save_log(data, tweet):
    log = BASE / "history.jsonl"
    entry = {"tweet": tweet, "data": data}
    with open(log, "a") as f:
        f.write(json.dumps(entry) + "\n")

# ─── MAIN PIPELINE ────────────────────────────────────
def run():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\n{'='*60}")
    print(f"🤖 Crypto Content Engine — {ts}")
    print(f"{'='*60}")
    
    # 1. Scrape
    print("📊 Scraping BTC data...")
    data = scrape()
    print(f"   BTC: ${data.get('price_usd'):,.0f} | 24h: {data.get('change_24h'):+.1f}% | FG: {data.get('fear_greed')}")
    
    # 2. Analyze
    print("🧠 Analyzing with AI...")
    tweet = analyze(data)
    print(f"   Tweet: {tweet[:100]}...")
    
    # 3. Generate meme
    print("🎨 Generating meme...")
    meme_ok = generate_meme(tweet, data)
    print(f"   Meme: {'✅' if meme_ok else '❌ (skipped)'}")
    
    # 4. Publish
    print("🐦 Publishing to X...")
    pub_ok = publish(tweet)
    
    # 5. Save
    save_log(data, tweet)
    print(f"\n✅ Pipeline complete. Tweet: {'published' if pub_ok else 'logged'}")
    
    return {"tweet": tweet, "data": data, "published": pub_ok}

if __name__ == "__main__":
    run()
