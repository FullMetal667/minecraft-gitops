#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

from common import (
    ensure_server_exists,
    overlay_kustomization,
    params_file,
    server_from_params_filename,
    upsert_env_value,
)


def update_image_tag(kustomization_path: Path, version: str) -> None:
    content = kustomization_path.read_text(encoding="utf-8")

    patterns = [
        r"(?m)^(\s*newTag:\s*)([^\s]+)\s*$",
        r"(?m)^(\s*tag:\s*)([^\s]+)\s*$",
    ]

    for pattern in patterns:
        new_content, count = re.subn(pattern, rf"\g<1>{version}", content, count=1)
        if count > 0:
            kustomization_path.write_text(new_content, encoding="utf-8")
            print(f"Updated image tag in {kustomization_path} -> {version}")
            return

    raise RuntimeError(
        f"Kein newTag:/tag: Eintrag in {kustomization_path} gefunden. "
        f"Bitte kustomization.yaml prüfen."
    )


def main() -> int:
    if len(sys.argv) < 4:
        print("Usage: python3 update_server.py <server|params-file> <version> <file_id> [zip]")
        return 1

    server = server_from_params_filename(sys.argv[1])
    version = sys.argv[2]
    file_id = sys.argv[3]
    zip_name = sys.argv[4] if len(sys.argv) >= 5 else None

    ensure_server_exists(server)

    env_file = params_file(server)
    kust_file = overlay_kustomization(server)

    upsert_env_value(env_file, "VERSION", version)
    upsert_env_value(env_file, "FILE_ID", file_id)

    if zip_name:
        upsert_env_value(env_file, "ZIP", zip_name)

    update_image_tag(kust_file, version)

    print(f"Server '{server}' erfolgreich aktualisiert:")
    print(f"  - {env_file}")
    print(f"  - {kust_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())