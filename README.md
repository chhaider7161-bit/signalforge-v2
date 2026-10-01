# SignalForge v2

A web-based, signal-only market dashboard.

## What it does
- Select an asset and expiry.
- Generate a rule-based CALL/UP or PUT/DOWN signal when the setup passes the configured threshold.
- View signal strength, entry price, reason, pending status and completed results.
- Optional Telegram notifications.
- Clearly labels synthetic DEMO data versus a configured external feed.

> Important: DEMO mode uses synthetic candles for testing the application. It is not real market data and does not guarantee trading outcomes. The app does not place trades.

## Deploy as a website

This repository includes `render.yaml` for Render Web Service deployment. Render supports Docker deployments from GitHub repositories and can automatically redeploy when the linked branch changes.

After deployment, open the service URL and use the dashboard. The `/health` endpoint reports whether DEMO mode is enabled.

For a live data source, set `DEMO_MODE=false` only after configuring an authorized market-data feed in `app/feed.py`.

## Local Docker

    docker compose up --build

Then open `http://localhost:8000`.

## Telegram
Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in the service environment.
