#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import time
from typing import Any

from common import REPO_ROOT
from state_store import find_release, upsert_release
from telegram_api import TelegramAPI


def run_cmd(args: list[str]) -> subprocess.CompletedProcess:
    print("> " + " ".join(args))
    return subprocess.run(args, text=True, capture_output=True, cwd=REPO_ROOT)


def truncate(text: str, limit: int = 3000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...\n(truncated)"


def build_merge_keyboard(release_id: str) -> dict[str, Any]:
    return {
        "inline_keyboard": [[
            {"text": "🚀 Merge ausführen", "callback_data": f"merge:{release_id}"},
            {"text": "❌ Abbrechen", "callback_data": f"cancel:{release_id}"},
        ]]
    }


def build_prepare_keyboard(release_id: str) -> dict[str, Any]:
    return {
        "inline_keyboard": [[
            {"text": "✅ Update vorbereiten", "callback_data": f"prepare:{release_id}"},
            {"text": "❌ Ignorieren", "callback_data": f"cancel:{release_id}"},
        ]]
    }


def format_prepare_summary(release: dict[str, Any], summary: dict[str, Any]) -> str:
    diff_text = summary.get("diff") or "Kein Diff vorhanden"

    return (
        f"✅ Release vorbereitet\n\n"
        f"Server: {release['server']}\n"
        f"Aktuell: {release['current_version']}\n"
        f"Neu: {release['new_version']}\n"
        f"File ID: {release['file_id']}\n"
        f"Branch: {summary['branch']}\n"
        f"Commit erstellt: {'ja' if summary.get('committed') else 'nein'}\n"
        f"Dateien:\n- " + "\n- ".join(summary["changed_files"]) + "\n\n"
        f"Diff:\n{truncate(diff_text, 1800)}\n\n"
        f"Merge jetzt durchführen?"
    )


def handle_prepare(release: dict[str, Any], api: TelegramAPI) -> None:
    release["status"] = "preparing"
    upsert_release(release)

    api.send_message(
        f"🔧 Prepare startet\n"
        f"Server: {release['server']}\n"
        f"Version: {release['new_version']}\n"
        f"File ID: {release['file_id']}"
    )

    result = run_cmd([
        "python3",
        "scripts/prepare_release.py",
        release["server"],
        release["new_version"],
        release["file_id"],
    ])

    if result.returncode != 0:
        release["status"] = "failed"
        release["prepare_stdout"] = truncate(result.stdout, 2000)
        release["prepare_stderr"] = truncate(result.stderr, 2000)
        upsert_release(release)

        api.send_message(
            f"❌ Prepare fehlgeschlagen\n\n"
            f"Server: {release['server']}\n"
            f"Version: {release['new_version']}\n\n"
            f"stdout:\n{truncate(result.stdout, 900)}\n\n"
            f"stderr:\n{truncate(result.stderr, 900)}"
        )
        return

    try:
        summary = json.loads(result.stdout)
    except json.JSONDecodeError:
        release["status"] = "failed"
        release["prepare_stdout"] = truncate(result.stdout, 2000)
        release["prepare_stderr"] = truncate(result.stderr, 2000)
        upsert_release(release)

        api.send_message(
            f"❌ Prepare lieferte kein gültiges JSON.\n\n"
            f"stdout:\n{truncate(result.stdout, 1500)}"
        )
        return

    release["status"] = "awaiting_merge_approval"
    release["prepare_summary"] = summary
    upsert_release(release)

    api.send_message(
        format_prepare_summary(release, summary),
        reply_markup=build_merge_keyboard(release["id"]),
    )


def handle_merge(release: dict[str, Any], api: TelegramAPI) -> None:
    release["status"] = "merging"
    upsert_release(release)

    api.send_message(
        f"🚀 Merge startet\n"
        f"Server: {release['server']}\n"
        f"Version: {release['new_version']}"
    )

    result = run_cmd([
        "python3",
        "scripts/merge_release.py",
        release["server"],
        release["new_version"],
        "--yes",
    ])

    if result.returncode != 0:
        release["status"] = "failed"
        release["merge_stdout"] = truncate(result.stdout, 2000)
        release["merge_stderr"] = truncate(result.stderr, 2000)
        upsert_release(release)

        api.send_message(
            f"❌ Merge fehlgeschlagen\n\n"
            f"Server: {release['server']}\n"
            f"Version: {release['new_version']}\n\n"
            f"stdout:\n{truncate(result.stdout, 900)}\n\n"
            f"stderr:\n{truncate(result.stderr, 900)}"
        )
        return

    try:
        merge_summary = json.loads(result.stdout)
    except json.JSONDecodeError:
        merge_summary = {"pr_url": "unbekannt"}

    release["status"] = "merged"
    release["merge_summary"] = merge_summary
    upsert_release(release)

    api.send_message(
        f"🎉 Merge erfolgreich\n\n"
        f"Server: {release['server']}\n"
        f"Version: {release['new_version']}\n"
        f"PR: {merge_summary.get('pr_url', '-')}"
    )


def handle_cancel(release: dict[str, Any], api: TelegramAPI) -> None:
    release["status"] = "cancelled"
    upsert_release(release)

    api.send_message(
        f"🛑 Vorgang abgebrochen\n\n"
        f"Server: {release['server']}\n"
        f"Version: {release['new_version']}"
    )


def handle_callback(callback_query: dict[str, Any], api: TelegramAPI) -> None:
    try:
        try:
            api.answer_callback_query(callback_query["id"], "Verstanden")
        except Exception as exc:
            print(f"Warning: answerCallbackQuery failed: {exc}")

        data = callback_query.get("data", "")
        if ":" not in data:
            print(f"Warning: invalid callback data: {data}")
            return

        action, release_id = data.split(":", 1)
        release = find_release(release_id)
        if not release:
            api.send_message(f"⚠️ Release nicht gefunden: {release_id}")
            return

        if action == "prepare":
            if release["status"] != "awaiting_prepare_approval":
                api.send_message(f"ℹ️ Release {release_id} ist bereits im Status {release['status']}.")
                return
            handle_prepare(release, api)
            return

        if action == "merge":
            if release["status"] != "awaiting_merge_approval":
                api.send_message(f"ℹ️ Release {release_id} ist bereits im Status {release['status']}.")
                return
            handle_merge(release, api)
            return

        if action == "cancel":
            handle_cancel(release, api)
            return

        api.send_message(f"⚠️ Unbekannte Aktion: {action}")

    except Exception as exc:
        print(f"Error while handling callback: {exc}")
        try:
            api.send_message(f"❌ Fehler beim Verarbeiten des Telegram-Callbacks:\n{exc}")
        except Exception:
            pass


def main() -> int:
    api = TelegramAPI()

    bootstrap = api.get_updates(timeout=1)
    results = bootstrap.get("result", [])
    offset: int | None = None

    if results:
        offset = results[-1]["update_id"] + 1

    print(f"Starting telegram bot with offset={offset}")

    while True:
        updates = api.get_updates(offset=offset, timeout=20)
        for update in updates.get("result", []):
            offset = update["update_id"] + 1

            if "callback_query" in update:
                handle_callback(update["callback_query"], api)

        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())