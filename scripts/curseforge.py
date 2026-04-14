#!/usr/bin/env python3
from __future__ import annotations

import os
import re
from typing import Any

import requests


API_BASE = "https://api.curseforge.com/v1"


def _headers() -> dict[str, str]:
    api_key = os.environ.get("CURSEFORGE_API_KEY")
    if not api_key:
        raise RuntimeError("CURSEFORGE_API_KEY is not set.")
    return {"x-api-key": api_key}


def get_mod_files(project_id: str | int, page_size: int = 20) -> list[dict[str, Any]]:
    resp = requests.get(
        f"{API_BASE}/mods/{project_id}/files",
        headers=_headers(),
        params={"pageSize": page_size, "index": 0},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"]


def extract_version(display_name: str, file_name: str) -> str:
    candidates = [display_name or "", file_name or ""]

    patterns = [
        r'[-_ ]v?(\d+\.\d+(?:\.\d+)*)',
        r'\bv?(\d+\.\d+(?:\.\d+)*)\b',
    ]

    for text in candidates:
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return m.group(1)

    return "unknown"


def detect_latest_file(project_id: str | int) -> dict[str, Any]:
    files = get_mod_files(project_id, page_size=50)
    if not files:
        raise RuntimeError(f"No CurseForge files found for project_id={project_id}")

    files_sorted = sorted(files, key=lambda item: item["id"], reverse=True)
    latest = files_sorted[0]

    display_name = latest.get("displayName", "")
    file_name = latest.get("fileName", "")

    return {
        "file_id": str(latest["id"]),
        "display_name": display_name,
        "file_name": file_name,
        "version": extract_version(display_name, file_name),
        "download_url": latest.get("downloadUrl"),
    }