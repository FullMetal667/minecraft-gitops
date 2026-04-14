#!/usr/bin/env python3
from __future__ import annotations

import os
from typing import Any

import requests


class TelegramAPI:
    def __init__(self) -> None:
        self.token = os.environ["TELEGRAM_BOT_TOKEN"]
        self.default_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def _post(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        resp = requests.post(f"{self.base_url}/{method}", json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok", False):
            raise RuntimeError(f"Telegram API error on {method}: {data}")
        return data

    def _get(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = requests.get(f"{self.base_url}/{method}", params=params or {}, timeout=35)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok", False):
            raise RuntimeError(f"Telegram API error on {method}: {data}")
        return data

    def get_me(self) -> dict[str, Any]:
        return self._get("getMe")

    def get_updates(self, offset: int | None = None, timeout: int = 30) -> dict[str, Any]:
        params: dict[str, Any] = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        return self._get("getUpdates", params=params)

    def send_message(
        self,
        text: str,
        chat_id: str | int | None = None,
        reply_markup: dict[str, Any] | None = None,
        disable_web_page_preview: bool = True,
    ) -> dict[str, Any]:
        target_chat_id = chat_id if chat_id is not None else self.default_chat_id
        if not target_chat_id:
            raise RuntimeError("No chat_id provided and TELEGRAM_CHAT_ID is not set.")

        payload: dict[str, Any] = {
            "chat_id": str(target_chat_id),
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self._post("sendMessage", payload)

    def edit_message_text(
        self,
        chat_id: str | int,
        message_id: int,
        text: str,
        reply_markup: dict[str, Any] | None = None,
        disable_web_page_preview: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chat_id": str(chat_id),
            "message_id": message_id,
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self._post("editMessageText", payload)

    def answer_callback_query(self, callback_query_id: str, text: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        return self._post("answerCallbackQuery", payload)