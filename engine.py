import math
from statistics import mean

class SignalEngine:
    """
    Transparent, rule-based signal scorer.
    Strength is a model score, NOT a probability of winning.
    """

    def analyze(self, candles, price):
        closes = [x["close"] for x in candles]
        highs = [x["high"] for x in candles]
        lows = [x["low"] for x in candles]
        if len(closes) < 60:
            return None

        ema9 = self.ema(closes, 9)
        ema21 = self.ema(closes, 21)
        ema50 = self.ema(closes, 50)
        rsi = self.rsi(closes, 14)
        macd, signal = self.macd(closes)
        bb_mid, bb_upper, bb_lower = self.bollinger(closes, 20, 2)
        atr = self.atr(highs, lows, closes, 14)

        score_up = 0
        score_down = 0
        reasons_up, reasons_down = [], []

        if ema9 > ema21 > ema50:
            score_up += 22; reasons_up.append("EMA trend aligned")
        elif ema9 < ema21 < ema50:
            score_down += 22; reasons_down.append("EMA trend aligned")

        if rsi >= 52 and rsi <= 72:
            score_up += 18; reasons_up.append(f"RSI {rsi:.1f}")
        elif rsi <= 48 and rsi >= 28:
            score_down += 18; reasons_down.append(f"RSI {rsi:.1f}")

        if macd > signal:
            score_up += 18; reasons_up.append("MACD bullish")
        elif macd < signal:
            score_down += 18; reasons_down.append("MACD bearish")

        if price > bb_mid:
            score_up += 12; reasons_up.append("above BB midline")
        elif price < bb_mid:
            score_down += 12; reasons_down.append("below BB midline")

        # Short momentum
        momentum = closes[-1] - closes[-6]
        if momentum > 0:
            score_up += 10; reasons_up.append("positive momentum")
        elif momentum < 0:
            score_down += 10; reasons_down.append("negative momentum")

        # Last candle body direction
        if closes[-1] > candles[-1]["open"]:
            score_up += 8; reasons_up.append("bullish candle")
        elif closes[-1] < candles[-1]["open"]:
            score_down += 8; reasons_down.append("bearish candle")

        # Volatility filter: avoid extremely flat markets.
        recent_range = mean([x["high"] - x["low"] for x in candles[-10:]])
        if atr > 0 and recent_range >= atr * 0.45:
            if score_up > score_down:
                score_up += 12
            elif score_down > score_up:
                score_down += 12

        if max(score_up, score_down) < 62:
            return None

        if score_up > score_down:
            return {
                "direction": "CALL",
                "strength": min(99.0, float(score_up)),
                "reason": "; ".join(reasons_up),
            }
        return {
            "direction": "PUT",
            "strength": min(99.0, float(score_down)),
            "reason": "; ".join(reasons_down),
        }

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
            gains.append(max(d, 0))
            losses.append(max(-d, 0))
        ag = sum(gains) / period
        al = sum(losses) / period
        if al == 0:
            return 100
        return 100 - (100 / (1 + ag / al))

    def macd(self, values):
        fast = self.ema(values, 12)
        slow = self.ema(values, 26)
        macd = fast - slow
        # Lightweight signal approximation over recent MACD values.
        series = []
        for i in range(26, len(values) + 1):
            f = self.ema(values[:i], 12)
            s = self.ema(values[:i], 26)
            series.append(f - s)
        signal = self.ema(series, 9)
        return macd, signal

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
