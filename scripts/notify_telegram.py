#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import requests


def send_telegram(message: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Telegram nicht konfiguriert: TELEGRAM_BOT_TOKEN oder TELEGRAM_CHAT_ID fehlt.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    resp = requests.post(url, json=payload, timeout=20)
    resp.raise_for_status()


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 notify_telegram.py '<message>'")
        return 1

    message = " ".join(sys.argv[1:])
    send_telegram(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())