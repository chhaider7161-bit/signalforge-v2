import random
import time
from collections import defaultdict, deque

class FeedManager:
    """
    Market-data abstraction. DEMO_MODE uses synthetic candles only.
    Production requires an authorized high-frequency market-data source.
    """

    def __init__(self, demo_mode=True):
        self.demo_mode = demo_mode
        self.prices = {}
        self.history = defaultdict(lambda: deque(maxlen=500))
        self.base = {
            "EURUSD": 1.0820, "GBPUSD": 1.2740, "USDJPY": 149.80, "AUDUSD": 0.6550,
            "EURUSD_OTC": 1.0820, "GBPUSD_OTC": 1.2740,
            "USDJPY_OTC": 149.80, "AUDUSD_OTC": 0.6550,
        }
        self.seeded = set()

    def _step(self, symbol):
        p = self.prices.get(symbol, self.base.get(symbol, 1.0))
        base = self.base.get(symbol, p)
        drift = (base - p) * 0.002
        shock = random.gauss(0, max(abs(p) * 0.00008, 0.000001))
        return p + drift + shock

    def _seed(self, symbol, count=120):
        if symbol in self.seeded:
            return
        p = self.base.get(symbol, 1.0)
        now = int(time.time())
        start = now - count
        for i in range(count):
            o = p
            c = p + random.gauss(0, max(abs(p) * 0.00008, 0.000001))
            h = max(o, c) + abs(random.gauss(0, max(abs(p) * 0.00003, 0.0000005)))
            l = min(o, c) - abs(random.gauss(0, max(abs(p) * 0.00003, 0.0000005)))
            self.history[symbol].append({"time": start+i, "open": o, "high": h, "low": l, "close": c})
            p = c
        self.prices[symbol] = p
        self.seeded.add(symbol)

    async def update(self, symbol):
        if not self.demo_mode:
            return
        self._seed(symbol)
        new = self._step(symbol)
        self.prices[symbol] = new
        now = int(time.time())
        if not self.history[symbol] or self.history[symbol][-1]["time"] != now:
            self.history[symbol].append({"time": now, "open": new, "high": new, "low": new, "close": new})
        else:
            c = self.history[symbol][-1]
            c["high"] = max(c["high"], new); c["low"] = min(c["low"], new); c["close"] = new

    async def price(self, symbol):
        await self.update(symbol)
        return self.prices.get(symbol)

    async def candles(self, symbol, limit=120):
        await self.update(symbol)
        return list(self.history[symbol])[-limit:]

