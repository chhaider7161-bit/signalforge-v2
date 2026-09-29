# SignalForge — Quotex-style Signal Dashboard

A deployable, signal-only web application with:

- FastAPI backend
- Python rule-based signal engine
- SQLite signal history
- Real calculated WIN/LOSS statistics
- Telegram alerts
- OTC asset slots
- 10s / 30s / 1m expiry selection
- Responsive dashboard
- Docker deployment

## Important data-feed note

The included `DEMO_MODE=true` feed is synthetic. It is included so the application can be run and tested immediately.

It does NOT represent Quotex prices and it must not be used as evidence that a strategy works on Quotex.

For production, replace `app/feed.py` with a market-data adapter you are authorized to use. For 10-second and 30-second expiry, the feed must provide sufficiently granular data. For OTC symbols, the source must actually publish the relevant OTC quotes.

This project never places a trade on Quotex.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open http://localhost:8000

On Windows PowerShell, use:
```powershell
Copy-Item .env.example .env
```

## Telegram

1. Create a bot using Telegram's BotFather.
2. Put the bot token in `.env` as `TELEGRAM_BOT_TOKEN`.
3. Put your target chat/channel ID in `TELEGRAM_CHAT_ID`.
4. Restart the server.

If Telegram credentials are empty, the dashboard still works.

## Docker

```bash
cp .env.example .env
docker compose up -d --build
```

Open:
http://localhost:8000

## Production checklist

Before using real-money decisions:

1. Replace the demo feed.
2. Use a licensed/authorized high-frequency market-data source.
3. Implement historical tick/second data for meaningful 10s/30s backtests.
4. Record the exact source timestamp and quote used for entry and expiry.
5. Run a long out-of-sample backtest.
6. Paper-test the live feed.
7. Keep the real WIN/LOSS calculation independent of the model's strength score.
8. Do not expose `.env` or Telegram credentials publicly.
9. Put the API behind HTTPS and authentication if exposed to the internet.
10. Add rate limiting and user authentication before opening it to other users.

## Architecture

Browser → FastAPI → SignalEngine + FeedManager → SQLite
                                   ↘ Telegram

The signal endpoint only creates a signal record. There is no trade-placement API.
