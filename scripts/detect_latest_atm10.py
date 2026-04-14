import os
import re
import sys
from typing import Optional

import requests

API_BASE = "https://api.curseforge.com/v1"
MOD_ID = 925200
VERSION_PATTERN = re.compile(r"All the Mods 10-(\d+(?:\.\d+)+)")


def version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def get_latest_server_file() -> tuple[str, int]:
    api_key = os.environ.get("CURSEFORGE_API_KEY")
    if not api_key:
        raise RuntimeError("CURSEFORGE_API_KEY is not set")

    headers = {
        "Accept": "application/json",
        "x-api-key": api_key,
    }

    url = f"{API_BASE}/mods/{MOD_ID}/files"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    payload = resp.json()
    files = payload.get("data", [])

    candidates: list[tuple[tuple[int, ...], str, int]] = []

    for item in files:
        if not item.get("isAvailable", False):
            continue

        if item.get("releaseType") != 1:
            continue

        display_name = item.get("displayName", "")
        file_name = item.get("fileName", "")

        match = VERSION_PATTERN.search(display_name) or VERSION_PATTERN.search(file_name)
        if not match:
            continue

        version = match.group(1)
        server_pack_file_id = item.get("serverPackFileId")

        if not server_pack_file_id:
            continue

        candidates.append((version_key(version), version, int(server_pack_file_id)))

    if not candidates:
        raise RuntimeError("No suitable ATM10 release with serverPackFileId found")

    candidates.sort(reverse=True)
    _, version, file_id = candidates[0]
    return version, file_id


if __name__ == "__main__":
    try:
        version, file_id = get_latest_server_file()
        print(f"VERSION={version}")
        print(f"FILE_ID={file_id}")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)