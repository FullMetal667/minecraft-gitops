#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from common import BUILD_DIR, load_env_file, server_from_params_filename
from curseforge import detect_latest_file
from state_store import find_release, upsert_release
from telegram_api import TelegramAPI


def build_prepare_keyboard(release_id: str) -> dict:
    return {
        "inline_keyboard": [[
            {"text": "✅ Update vorbereiten", "callback_data": f"prepare:{release_id}"},
            {"text": "❌ Ignorieren", "callback_data": f"cancel:{release_id}"},
        ]]
    }


def main() -> int:
    api = TelegramAPI()

    for env_path in sorted(Path(BUILD_DIR).glob("params-*.env")):
        server = server_from_params_filename(env_path.name)
        env = load_env_file(env_path)

        project_id = env.get("CURSEFORGE_PROJECT_ID")
        current_version = env.get("VERSION", env.get("IMAGE_TAG", "unknown"))
        current_file_id = env.get("FILE_ID")

        if not project_id or not current_file_id:
            print(f"Skipping {env_path}: CURSEFORGE_PROJECT_ID or FILE_ID missing")
            continue

        latest = detect_latest_file(project_id)
        new_file_id = latest["file_id"]

        if str(current_file_id) == str(new_file_id):
            print(f"{server}: already up to date ({current_version}, file_id={current_file_id})")
            continue

        release_id = f"{server}-{new_file_id}"
        if find_release(release_id):
            print(f"{server}: release already known: {release_id}")
            continue

        release = {
            "id": release_id,
            "server": server,
            "current_version": current_version,
            "new_version": latest["version"],
            "file_id": new_file_id,
            "file_name": latest.get("file_name"),
            "status": "awaiting_prepare_approval",
        }
        upsert_release(release)

        text = (
            f"📦 Neues CurseForge-Update gefunden\n\n"
            f"Server: {server}\n"
            f"Aktuell: {current_version}\n"
            f"Verfügbar: {release['new_version']}\n"
            f"File ID: {new_file_id}\n"
            f"Datei: {release.get('file_name') or '-'}\n\n"
            f"Update vorbereiten?"
        )

        api.send_message(text, reply_markup=build_prepare_keyboard(release_id))
        print(f"Notified for {release_id}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())