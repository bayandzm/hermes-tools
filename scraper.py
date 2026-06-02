import json, sys
import urllib.request as ur
from datetime import datetime

def fetch(url):
    try:
        req = ur.Request(url, headers={"User-Agent": "CryptoBot/1.0"})
        with ur.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except: return {}

btc = fetch("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true")
fg = fetch("https://api.alternative.me/fng/?limit=1")
total = fetch("https://api.coingecko.com/api/v3/global")

result = {
    "ts": datetime.utcnow().isoformat(),
    "price": btc.get("bitcoin", {}).get("usd"),
    "change_24h": btc.get("bitcoin", {}).get("usd_24h_change"),
    "fear_greed": int(fg.get("data", [{}])[0].get("value", 50)),
    "fear_greed_label": fg.get("data", [{}])[0].get("value_classification", "N"),
    "dominance": total.get("data", {}).get("market_cap_percentage", {}).get("btc"),
}

print(json.dumps(result, indent=2))
