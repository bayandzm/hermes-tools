# Hermes Tools API

Public API for crypto data, Polymarket markets, and AI image generation.
Monetize: $10-50/month per developer.

## Quick Deploy

### Docker
```bash
docker build -t hermes-tools .
docker run -p 8765:8765 -e HF_TOKEN=your_hftoken hermes-tools
```

### Manual
```bash
pip install fastapi uvicorn
python api_server.py 8765
```

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/btc` | BTC price, volume, 24h change |
| GET | `/api/fear-greed` | Fear & Greed Index |
| GET | `/api/dominance` | BTC market dominance |
| GET | `/api/summary` | All crypto data in one call |
| GET | `/api/polymarket?limit=5` | Top Polymarket markets |
| POST | `/api/generate?prompt=...&token=...` | AI image generation |

## MCP Server (for AI agents)

```yaml
# ~/.hermes/config.yaml
mcp_servers:
  hermes-tools:
    command: "python3"
    args: ["mcp_server.py"]
```

## Pricing

- **Free tier**: 100 requests/day
- **Pro ($10/mo)**: 1000 requests/day + image gen (20/day)
- **Team ($50/mo)**: unlimited + priority support

Contact: @hermes_coree_bot on Telegram
