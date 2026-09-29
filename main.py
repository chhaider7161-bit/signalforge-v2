import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.database import init_db, SessionLocal, Signal
from app.engine import SignalEngine
from app.feed import FeedManager
from app.telegram_bot import TelegramNotifier

load_dotenv()

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
ENGINE_INTERVAL = int(os.getenv("ENGINE_INTERVAL_SECONDS", "2"))

feed = FeedManager(demo_mode=DEMO_MODE)
engine = SignalEngine()
telegram = TelegramNotifier()

ASSETS = [
    {"symbol": "EURUSD", "name": "EUR/USD", "otc": False},
    {"symbol": "GBPUSD", "name": "GBP/USD", "otc": False},
    {"symbol": "USDJPY", "name": "USD/JPY", "otc": False},
    {"symbol": "AUDUSD", "name": "AUD/USD", "otc": False},
    {"symbol": "EURUSD_OTC", "name": "EUR/USD OTC", "otc": True},
    {"symbol": "GBPUSD_OTC", "name": "GBP/USD OTC", "otc": True},
    {"symbol": "USDJPY_OTC", "name": "USD/JPY OTC", "otc": True},
    {"symbol": "AUDUSD_OTC", "name": "AUD/USD OTC", "otc": True},
]

async def market_loop():
    while True:
        try:
            # Keep prices/ticks moving and settle pending signals.
            for asset in ASSETS:
                await feed.update(asset["symbol"])
            db = SessionLocal()
            try:
                pending = db.query(Signal).filter(Signal.status == "PENDING").all()
                now = datetime.now(timezone.utc)
                for s in pending:
                    if now >= s.expiry_at:
                        price = await feed.price(s.asset_symbol)
                        if price is None:
                            continue
                        s.exit_price = price
                        if s.direction == "CALL":
                            s.status = "WIN" if price > s.entry_price else "LOSS"
                        else:
                            s.status = "WIN" if price < s.entry_price else "LOSS"
                        s.closed_at = now
                db.commit()
            finally:
                db.close()
        except Exception as exc:
            print("market_loop:", exc)
        await asyncio.sleep(ENGINE_INTERVAL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(market_loop())
    yield
    task.cancel()

app = FastAPI(title="SignalForge Quotex Signal Dashboard", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(open("app/static/index.html", encoding="utf-8").read())

@app.get("/api/assets")
async def assets():
    return ASSETS

@app.get("/api/stats")
async def stats():
    db = SessionLocal()
    try:
        total = db.query(Signal).filter(Signal.status.in_(["WIN","LOSS"])).count()
        wins = db.query(Signal).filter(Signal.status == "WIN").count()
        losses = db.query(Signal).filter(Signal.status == "LOSS").count()
        pending = db.query(Signal).filter(Signal.status == "PENDING").count()
        win_rate = round((wins / total) * 100, 2) if total else 0.0
        return {"total": total, "wins": wins, "losses": losses, "pending": pending, "win_rate": win_rate}
    finally:
        db.close()

@app.get("/api/signals")
async def signals(limit: int = 50):
    db = SessionLocal()
    try:
        rows = db.query(Signal).order_by(Signal.created_at.desc()).limit(min(limit, 200)).all()
        return [r.to_dict() for r in rows]
    finally:
        db.close()

@app.post("/api/signal")
async def generate_signal(payload: dict):
    symbol = payload.get("symbol", "EURUSD")
    expiry = int(payload.get("expiry_seconds", 60))
    if expiry not in (10, 30, 60):
        return {"error": "expiry_seconds must be 10, 30, or 60"}

    asset = next((a for a in ASSETS if a["symbol"] == symbol), None)
    if not asset:
        return {"error": "Unknown asset"}

    candles = await feed.candles(symbol, 120)
    price = await feed.price(symbol)
    if price is None or len(candles) < 60:
        return {"error": "Not enough market data"}

    result = engine.analyze(candles, price)
    if not result:
        return {"error": "No sufficiently strong setup"}

    now = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        s = Signal(
            asset_symbol=symbol,
            asset_name=asset["name"],
            is_otc=asset["otc"],
            direction=result["direction"],
            strength=result["strength"],
            entry_price=price,
            expiry_seconds=expiry,
            created_at=now,
            expiry_at=now,
            status="PENDING",
        )
        # Avoid datetime arithmetic surprises and keep UTC-aware values.
        from datetime import timedelta
        s.expiry_at = now + timedelta(seconds=expiry)
        s.reason = result["reason"]
        db.add(s)
        db.commit()
        db.refresh(s)
        signal = s.to_dict()
    finally:
        db.close()

    await telegram.send_signal(signal)
    return signal

@app.get("/health")
async def health():
    return {"ok": True, "demo_mode": DEMO_MODE}
