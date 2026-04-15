#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from common import load_env_file
from curseforge import detect_latest_file


def main():
    build_dir = Path("build")

    for env_path in sorted(build_dir.glob("params-*.env")):
        server = env_path.stem.replace("params-", "")
        env = load_env_file(env_path)

        project_id = env.get("CURSEFORGE_PROJECT_ID")
        current_file_id = env.get("FILE_ID")
        current_version = env.get("VERSION", env.get("IMAGE_TAG", "unknown"))

        if not project_id or not current_file_id:
            print(f"{server}: ❌ missing project_id or file_id")
            continue

        try:
            latest = detect_latest_file(project_id)
        except Exception as e:
            print(f"{server}: ❌ error fetching from CurseForge: {e}")
            continue

        latest_version = latest["version"]
        latest_file_id = latest["file_id"]

        if str(current_file_id) == str(latest_file_id):
            status = "✅ up-to-date"
        else:
            status = "🚀 update available"

        print(f"\n=== {server} ===")
        print(f"current version : {current_version}")
        print(f"current file_id : {current_file_id}")
        print(f"latest version  : {latest_version}")
        print(f"latest file_id  : {latest_file_id}")
        print(f"status          : {status}")


if __name__ == "__main__":
    main()