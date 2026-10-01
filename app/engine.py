from statistics import mean

class SignalEngine:
    """Transparent rule-based scorer. Strength is a score, not a win probability."""

    def analyze(self, candles, price):
        closes = [x["close"] for x in candles]
        highs = [x["high"] for x in candles]
        lows = [x["low"] for x in candles]
        if len(closes) < 60:
            return None

        ema9, ema21, ema50 = self.ema(closes, 9), self.ema(closes, 21), self.ema(closes, 50)
        rsi = self.rsi(closes, 14)
        macd, signal = self.macd(closes)
        bb_mid, _, _ = self.bollinger(closes, 20, 2)
        atr = self.atr(highs, lows, closes, 14)

        up = down = 0
        reasons_up, reasons_down = [], []

        if ema9 > ema21 > ema50:
            up += 22; reasons_up.append("EMA trend aligned")
        elif ema9 < ema21 < ema50:
            down += 22; reasons_down.append("EMA trend aligned")

        if 52 <= rsi <= 72:
            up += 18; reasons_up.append(f"RSI {rsi:.1f}")
        elif 28 <= rsi <= 48:
            down += 18; reasons_down.append(f"RSI {rsi:.1f}")

        if macd > signal:
            up += 18; reasons_up.append("MACD bullish")
        elif macd < signal:
            down += 18; reasons_down.append("MACD bearish")

        if price > bb_mid:
            up += 12; reasons_up.append("above BB midline")
        elif price < bb_mid:
            down += 12; reasons_down.append("below BB midline")

        momentum = closes[-1] - closes[-6]
        if momentum > 0:
            up += 10; reasons_up.append("positive momentum")
        elif momentum < 0:
            down += 10; reasons_down.append("negative momentum")

        if closes[-1] > candles[-1]["open"]:
            up += 8; reasons_up.append("bullish candle")
        elif closes[-1] < candles[-1]["open"]:
            down += 8; reasons_down.append("bearish candle")

        recent_range = mean(x["high"] - x["low"] for x in candles[-10:])
        if atr > 0 and recent_range >= atr * 0.45:
            if up > down: up += 12
            elif down > up: down += 12

        score = max(up, down)
        if score < 62 or up == down:
            return None

        if up > down:
            return {"direction": "CALL", "strength": min(99.0, float(up)), "reason": "; ".join(reasons_up)}
        return {"direction": "PUT", "strength": min(99.0, float(down)), "reason": "; ".join(reasons_down)}

    @staticmethod
    def ema(values, period):
        k = 2 / (period + 1)
        e = values[0]
        for v in values[1:]:
            e = v * k + e * (1 - k)
        return e

    @staticmethod
    def rsi(values, period=14):
        gains, losses = [], []
        for a, b in zip(values[-period-1:-1], values[-period:]):
            d = b - a
            gains.append(max(d, 0)); losses.append(max(-d, 0))
        ag, al = sum(gains) / period, sum(losses) / period
        if al == 0: return 100.0
        return 100 - (100 / (1 + ag / al))

    def macd(self, values):
        series = []
        for i in range(26, len(values) + 1):
            series.append(self.ema(values[:i], 12) - self.ema(values[:i], 26))
        return series[-1], self.ema(series, 9)

    def bollinger(self, values, period=20, mult=2):
        x = values[-period:]
        m = mean(x)
        sd = (sum((v-m)**2 for v in x) / period) ** 0.5
        return m, m + mult*sd, m - mult*sd

    @staticmethod
    def atr(highs, lows, closes, period=14):
        trs = []
        for i in range(1, len(closes)):
            trs.append(max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1])))
        return sum(trs[-period:]) / period
