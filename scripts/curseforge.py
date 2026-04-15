#!/usr/bin/env python3
from __future__ import annotations

import os
import requests

API_BASE = "https://api.curseforge.com/v1"
GAME_ID_MINECRAFT = 432


def _headers():
    return {
        "Accept": "application/json",
        "x-api-key": os.environ["CURSEFORGE_API_KEY"],
    }


def _get(path, params=None):
    resp = requests.get(
        f"{API_BASE}{path}",
        headers=_headers(),
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"]


def get_project_by_slug(slug: str) -> dict:
    data = _get(
        "/mods/search",
        params={
            "gameId": GAME_ID_MINECRAFT,
            "slug": slug,
            "pageSize": 1,
        },
    )
    if not data:
        raise RuntimeError(f"Projekt nicht gefunden: {slug}")
    return data[0]


def get_project(project_id: int) -> dict:
    return _get(f"/mods/{project_id}")


def get_files(mod_id: int, mc_version: str | None = None):
    params = {"pageSize": 50}
    if mc_version:
        params["gameVersion"] = mc_version

    files = _get(f"/mods/{mod_id}/files", params=params)
    return sorted(files, key=lambda x: x.get("fileDate", ""), reverse=True)


def get_latest_client_file(mod_id: int, mc_version: str | None = None):
    files = get_files(mod_id, mc_version)

    for f in files:
        name = (f.get("fileName") or "").lower()
        display = (f.get("displayName") or "").lower()

        if "server" in name or "server" in display:
            continue

        return f

    raise RuntimeError(f"Keine Client-Datei für Mod-ID {mod_id} gefunden")


def get_file_details(mod_id: int, file_id: int):
    return _get(f"/mods/{mod_id}/files/{file_id}")


def extract_version_token(display_name: str) -> str | None:
    parts = display_name.replace("(", " ").replace(")", " ").split()

    for part in reversed(parts):
        if any(c.isdigit() for c in part):
            return part.lower()

    return None


def find_server_file_id(mod_id: int, client_file: dict) -> int:
    client_id = client_file["id"]
    details = get_file_details(mod_id, client_id)

    for key in ("serverPackFileId", "serverFileId", "alternateFileId"):
        value = details.get(key)
        if isinstance(value, int) and value > 0 and value != client_id:
            return value

    client_name = (client_file.get("displayName") or "").lower()
    client_date = client_file.get("fileDate", "")
    version_token = extract_version_token(client_name)

    files = get_files(mod_id)

    candidates = []
    for f in files:
        name = (f.get("fileName") or "").lower()
        display = (f.get("displayName") or "").lower()

        if "server" not in name and "server" not in display:
            continue

        score = 0
        if version_token and version_token in name:
            score += 3
        if version_token and version_token in display:
            score += 3
        if client_date and f.get("fileDate", "")[:10] == client_date[:10]:
            score += 2

        candidates.append((score, f))

    candidates.sort(key=lambda x: (x[0], x[1].get("fileDate", "")), reverse=True)

    if candidates and candidates[0][0] > 0:
        return candidates[0][1]["id"]

    raise RuntimeError(f"Keine Server-Datei für Client-File {client_id} gefunden")


def _resolve_release_for_mod(mod_id: int, project_name: str, mc_version: str | None = None) -> dict:
    client_file = get_latest_client_file(mod_id, mc_version)
    server_file_id = find_server_file_id(mod_id, client_file)

    version = (
        extract_version_token(client_file.get("displayName", ""))
        or client_file.get("displayName")
        or "unknown"
    )

    return {
        "project_id": mod_id,
        "project_name": project_name,
        "version": version,
        "client_file_id": client_file["id"],
        "server_file_id": server_file_id,
        "display_name": client_file.get("displayName"),
        "file_name": client_file.get("fileName"),
        "file_date": client_file.get("fileDate"),
    }


def resolve_release(slug: str, mc_version: str | None = None) -> dict:
    project = get_project_by_slug(slug)
    return _resolve_release_for_mod(
        mod_id=project["id"],
        project_name=project["name"],
        mc_version=mc_version,
    )


def resolve_release_by_project_id(project_id: int, mc_version: str | None = None) -> dict:
    project = get_project(project_id)
    return _resolve_release_for_mod(
        mod_id=project["id"],
        project_name=project["name"],
        mc_version=mc_version,
    )