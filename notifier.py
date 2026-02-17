"""
notifier.py
Sends Telegram alerts for newly found jobs.
"""

import os
import requests

# ─── Configuration ────────────────────────────────────────────────────────────
# Set these as environment variables (GitHub Secrets in Actions):
#   TELEGRAM_BOT_TOKEN  →  your bot token from @BotFather
#   TELEGRAM_CHAT_ID    →  your personal or group chat ID

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def send_alert(company: str, title: str, location: str, link: str):
    """
    Send a Telegram message for a newly detected job.
    Silently fails (prints error) so the script keeps running even if
    Telegram is temporarily unreachable.
    """
    if not BOT_TOKEN or not CHAT_ID:
        print("[Notifier] ⚠️  TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — skipping alert.")
        return

    message = (
        f"🚀 *New AI/SDE Job Alert!*\n\n"
        f"🏢 *Company:* {company}\n"
        f"💼 *Role:* {title}\n"
        f"📍 *Location:* {location or 'Not specified'}\n"
        f"🔗 [Apply Here]({link})"
    )

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }

    try:
        response = requests.post(TELEGRAM_URL, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"[Notifier] ✅ Alert sent → {title} @ {company}")
        else:
            print(f"[Notifier] ❌ Failed to send alert: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"[Notifier] ❌ Network error: {e}")
