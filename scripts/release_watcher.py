#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from common import BUILD_DIR, load_env_file, server_from_params_filename
from curseforge import resolve_release_by_project_id
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

        watch_enabled = env.get("RELEASE_WATCH_ENABLED", "true").strip().lower()
        if watch_enabled in {"false", "0", "no", "off"}:
            print(f"{server}: release watcher disabled")
            continue

        project_id = env.get("CURSEFORGE_PROJECT_ID")
        mc_version = env.get("MC_VERSION")
        current_version = env.get("VERSION", env.get("IMAGE_TAG", "unknown"))
        current_file_id = env.get("FILE_ID")

        if not project_id:
            print(f"Skipping {env_path}: CURSEFORGE_PROJECT_ID missing")
            continue

        if not current_file_id:
            print(f"Skipping {env_path}: FILE_ID missing")
            continue

        latest = resolve_release_by_project_id(int(project_id), mc_version=mc_version)

        new_client_file_id = str(latest["client_file_id"])
        new_server_file_id = str(latest["server_file_id"])
        new_version = str(latest["version"])

        if str(current_file_id) == new_server_file_id:
            print(
                f"{server}: already up to date "
                f"({current_version}, server_file_id={current_file_id})"
            )
            continue

        release_id = f"{server}-{new_server_file_id}"
        if find_release(release_id):
            print(f"{server}: release already known: {release_id}")
            continue

        release = {
            "id": release_id,
            "server": server,
            "current_version": current_version,
            "new_version": new_version,
            "client_file_id": new_client_file_id,
            "server_file_id": new_server_file_id,
            "display_name": latest.get("display_name"),
            "file_name": latest.get("file_name"),
            "status": "awaiting_prepare_approval",
        }
        upsert_release(release)

        text = (
            f"📦 Neues CurseForge-Update gefunden\n\n"
            f"Server: {server}\n"
            f"Aktuell: {current_version}\n"
            f"Verfügbar: {new_version}\n"
            f"Client File ID: {new_client_file_id}\n"
            f"Server File ID: {new_server_file_id}\n"
            f"Datei: {latest.get('display_name') or latest.get('file_name') or '-'}\n\n"
            f"Update vorbereiten?"
        )

        api.send_message(text, reply_markup=build_prepare_keyboard(release_id))
        print(f"Notified for {release_id}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())