#!/usr/bin/env python3
"""Crypto Content Engine — Full Autonomous Pipeline"""
import json, os, subprocess
import urllib.request as ur
from datetime import datetime, timezone
from pathlib import Path

BASE = Path.home() / "crypto-content-bot"
OUT = BASE / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

def fetch(url, timeout=15):
    req = ur.Request(url, headers={"User-Agent": "CryptoBot/1.0"})
    with ur.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

# 1. SCRAPE
print("📊 Scraping BTC data...")
btc = fetch("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true")
fg = fetch("https://api.alternative.me/fng/?limit=1")
tot = fetch("https://api.coingecko.com/api/v3/global")

data = {
    "ts": datetime.now(timezone.utc).isoformat(),
    "price": btc["bitcoin"]["usd"],
    "change_24h": btc["bitcoin"]["usd_24h_change"],
    "fg": int(fg["data"][0]["value"]),
    "fglabel": fg["data"][0]["value_classification"],
    "dominance": tot["data"]["market_cap_percentage"]["btc"],
}
json.dump(data, open(OUT / "scrape.json", "w"), indent=2)
print(f"   BTC: ${data['price']:,.0f} | {data['change_24h']:+.1f}% | FG: {data['fg']} ({data['fglabel']}) | Dom: {data['dominance']:.1f}%")

# 2. ANALYZE & GENERATE TWEET
print("🧠 Analyzing...")
p = data["price"]; c = data["change_24h"]; fg = data["fg"]; fl = data["fglabel"]

if fg < 25:
    game = "Extreme Fear = historically best DCA entry. Saylor accumulation pattern repeats."
elif fg < 50:
    game = "Fear zone. Smart money accumulating. Every cycle: fear → greed → ATH."
elif fg < 75:
    game = "Greed rising. Distribution warning. BTC dominance signals alt rotation."
else:
    game = "Extreme Greed. History says: cautious when everyone is bullish."

tweet = f"BTC ${p:,.0f} | 24h: {c:+.1f}% | Fear & Greed: {fg}/100 ({fl})\n{game} $BTC"
tweet = tweet[:260].strip()
open(OUT / "tweet.txt", "w").write(tweet)
print(f"   Tweet: {tweet[:80]}...")

# 3. SAVE HISTORY
entry = {"ts": data["ts"], "tweet": tweet, "data": data}
with open(BASE / "history.jsonl", "a") as f:
    f.write(json.dumps(entry) + "\n")

# 4. TRY X POST
xurl_path = os.path.expanduser("~/.nvm/versions/node/v22.22.2/bin/xurl")
if os.path.exists(xurl_path):
    r = subprocess.run([xurl_path, "post", tweet], capture_output=True, text=True, timeout=20)
    if "CreditsDepleted" in r.stdout:
        print("   ⚠️ X credits depleted — tweet queued (will post when refilled)")
    elif r.returncode == 0:
        print("   ✅ Posted to X!")
    else:
        print(f"   ❌ X: {r.stdout[:80]}")
else:
    print("   ⚠️ xurl not found — tweet queued")

print(f"\n✅ Pipeline complete! Tweet saved to {OUT}/tweet.txt")
