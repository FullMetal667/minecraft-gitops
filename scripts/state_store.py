#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = REPO_ROOT / "state" / "releases.json"


def _ensure_state_file() -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps({"releases": []}, indent=2), encoding="utf-8")


def load_state() -> dict[str, Any]:
    _ensure_state_file()
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    _ensure_state_file()
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def list_releases() -> list[dict[str, Any]]:
    return load_state()["releases"]


def find_release(release_id: str) -> dict[str, Any] | None:
    for item in list_releases():
        if item["id"] == release_id:
            return item
    return None


def upsert_release(release: dict[str, Any]) -> None:
    state = load_state()
    releases = state["releases"]

    for idx, item in enumerate(releases):
        if item["id"] == release["id"]:
            releases[idx] = release
            save_state(state)
            return

    releases.append(release)
    save_state(state)


def update_release_status(release_id: str, status: str) -> dict[str, Any]:
    state = load_state()
    for item in state["releases"]:
        if item["id"] == release_id:
            item["status"] = status
            save_state(state)
            return item
    raise KeyError(f"Release not found: {release_id}")