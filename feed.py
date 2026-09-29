import asyncio
import math
import os
import random
import time
from collections import defaultdict, deque

class FeedManager:
    """
    Data abstraction.

    DEMO_MODE=true:
      Generates a local synthetic tick/candle stream so the website works
      immediately. This is NOT Quotex market data.

    Production:
      Replace/update this adapter with a licensed high-frequency market data
      provider or a data source you are authorized to use. OTC symbols require
      a source that actually publishes the relevant OTC quotes.
    """

    def __init__(self, demo_mode=True):
        self.demo_mode = demo_mode
        self.prices = {}
        self.history = defaultdict(lambda: deque(maxlen=500))
        self.base = {
            "EURUSD": 1.0820, "GBPUSD": 1.2740, "USDJPY": 149.80,
            "AUDUSD": 0.6550,
            "EURUSD_OTC": 1.0820, "GBPUSD_OTC": 1.2740,
            "USDJPY_OTC": 149.80, "AUDUSD_OTC": 0.6550,
        }

    async def update(self, symbol):
        if not self.demo_mode:
            # A real adapter should populate self.prices/history here.
            return
        p = self.prices.get(symbol, self.base.get(symbol, 1.0))
        # Small mean-reverting random walk.
        drift = (self.base.get(symbol, p) - p) * 0.002
        shock = random.gauss(0, max(abs(p) * 0.00008, 0.000001))
        new = p + drift + shock
        self.prices[symbol] = new
        now = int(time.time())
        bucket = now - (now % 1)
        if not self.history[symbol] or self.history[symbol][-1]["time"] != bucket:
            self.history[symbol].append({
                "time": bucket, "open": new, "high": new, "low": new, "close": new
            })
        else:
            c = self.history[symbol][-1]
            c["high"] = max(c["high"], new)
            c["low"] = min(c["low"], new)
            c["close"] = new

    async def price(self, symbol):
        if self.demo_mode:
            await self.update(symbol)
            return self.prices.get(symbol)
        return self.prices.get(symbol)

    async def candles(self, symbol, limit=120):
        if self.demo_mode:
            for _ in range(max(0, limit - len(self.history[symbol]))):
                await self.update(symbol)
            return list(self.history[symbol])[-limit:]
        return list(self.history[symbol])[-limit:]
