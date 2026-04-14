#!/usr/bin/env python3
from __future__ import annotations

import shlex
import subprocess
import sys

from common import server_from_params_filename


def run(cmd: str) -> None:
    print(f"> {cmd}")
    subprocess.run(cmd, shell=True, check=True)


def notify(message: str) -> None:
    escaped = message.replace('"', '\\"')
    try:
        run(f'python3 scripts/notify_telegram.py "{escaped}"')
    except subprocess.CalledProcessError:
        print("Telegram-Notification fehlgeschlagen, Workflow läuft weiter.")


def main() -> int:
    if len(sys.argv) < 4:
        print("Usage: python3 prepare_release.py <server|params-file> <version> <file_id> [zip]")
        return 1

    raw_server = sys.argv[1]
    version = sys.argv[2]
    file_id = sys.argv[3]
    zip_name = sys.argv[4] if len(sys.argv) >= 5 else None

    server = server_from_params_filename(raw_server)

    notify(f"🚀 Release-Workflow gestartet\nServer: `{server}`\nVersion: `{version}`\nFile ID: `{file_id}`")

    cmd = f"python3 scripts/gitops.py {shlex.quote(server)} {shlex.quote(version)} {shlex.quote(file_id)}"
    if zip_name:
        cmd += f" {shlex.quote(zip_name)}"

    try:
        run(cmd)
    except subprocess.CalledProcessError as exc:
        notify(f"❌ Release fehlgeschlagen\nServer: `{server}`\nVersion: `{version}`")
        raise SystemExit(exc.returncode)

    notify(f"✅ Release vorbereitet\nServer: `{server}`\nVersion: `{version}`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())