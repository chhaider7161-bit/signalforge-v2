import os
import httpx

class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    async def send_signal(self, s):
        if not self.token or not self.chat_id:
            return
        direction = "🟢 CALL / UP" if s["direction"] == "CALL" else "🔴 PUT / DOWN"
        otc = " OTC" if s["is_otc"] else ""
        text = (
            "🚨 NEW SIGNAL\n\n"
            f"Asset: {s['asset_name']}{otc}\n"
            f"Direction: {direction}\n"
            f"Expiry: {s['expiry_seconds']}s\n"
            f"Entry: {s['entry_price']}\n"
            f"Strength: {s['strength']}%\n\n"
            "Signal only — no automatic trade."
        )
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                await client.post(url, json={"chat_id": self.chat_id, "text": text})
        except Exception as exc:
            print("telegram:", exc)
