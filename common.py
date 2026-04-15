#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Dict

REPO_ROOT = Path(__file__).resolve().parent
BUILD_DIR = REPO_ROOT / "build"
CLUSTERS_DIR = REPO_ROOT / "clusters"
BASE_DIR = CLUSTERS_DIR / "base"
OVERLAYS_DIR = CLUSTERS_DIR / "overlays"
CONFIG_DIR = REPO_ROOT / "config"
STATE_DIR = REPO_ROOT / "state"


def run(cmd: str, check: bool = True, capture_output: bool = False) -> subprocess.CompletedProcess:
    print(f"> {cmd}")
    return subprocess.run(
        cmd,
        shell=True,
        check=check,
        text=True,
        capture_output=capture_output,
        cwd=REPO_ROOT,
    )


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {path}")


def server_from_params_filename(value: str) -> str:
    """
    Erlaubt:
      - atm10
      - build/params-atm10.env
      - params-atm10.env
    """
    value = value.strip()

    m = re.search(r"params-([a-zA-Z0-9_-]+)\.env$", value)
    if m:
        return m.group(1)

    return value


def params_file(server: str) -> Path:
    return BUILD_DIR / f"params-{server}.env"


def overlay_dir(server: str) -> Path:
    return OVERLAYS_DIR / server


def overlay_kustomization(server: str) -> Path:
    return overlay_dir(server) / "kustomization.yaml"


def load_env_file(path: Path) -> Dict[str, str]:
    require_file(path)
    result: Dict[str, str] = {}

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[len("export "):].strip()

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        result[key] = value

    return result


def upsert_env_value(path: Path, key: str, value: str) -> None:
    require_file(path)

    lines = path.read_text(encoding="utf-8").splitlines()
    replaced = False
    new_lines = []

    for line in lines:
        if re.match(rf"^{re.escape(key)}=", line):
            new_lines.append(f"{key}={value}")
            replaced = True
        else:
            new_lines.append(line)

    if not replaced:
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.append(f"{key}={value}")

    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def ensure_server_exists(server: str) -> None:
    require_file(params_file(server))
    require_file(overlay_kustomization(server))