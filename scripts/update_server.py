#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

from common import (
    ensure_server_exists,
    load_env_file,
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


def strip_quotes(value: str) -> str:
    return value.strip().strip('"').strip("'")


def resolve_image_tag_placeholders(value: str, version: str) -> str:
    """
    Ersetzt typische Platzhalter mit der konkreten Version.
    """
    value = strip_quotes(value)
    value = value.replace("${IMAGE_TAG}", version)
    value = value.replace("$IMAGE_TAG", version)
    value = value.replace("${VERSION}", version)
    value = value.replace("$VERSION", version)
    return value


def looks_like_plain_version(value: str) -> bool:
    """
    Erkennt Werte wie 1.10.0 oder 2.5.3-beta.1 grob als 'nur Version'.
    """
    value = strip_quotes(value)
    return bool(re.fullmatch(r"[0-9]+(?:\.[0-9A-Za-z_-]+)+", value))


def default_zip_name(server: str, version: str) -> str:
    """
    Fallback, falls im params-File kein brauchbarer ZIP-Wert vorhanden ist.
    """
    mapping = {
        "sb4": f"ftb-stoneblock-4-{version}-server.zip",
        "aof7": f"All%20of%20Fabric%207-Server-{version}.zip",
    }
    return mapping.get(server, f"{server}-{version}.zip")


def default_dir_name(server: str, version: str) -> str:
    """
    Fallback, falls im params-File kein brauchbarer DIR-Wert vorhanden ist.
    """
    mapping = {
        "sb4": f"ftb-stoneblock-4-{version}-server",
        "aof7": f"All of Fabric 7-Server-{version}",
    }
    return mapping.get(server, f"{server}-{version}")


def resolve_zip_and_dir(server: str, version: str, env: dict[str, str], zip_name: str | None) -> tuple[str, str]:
    """
    Priorität:
    1. explizit übergebenes zip_name, wenn es nicht bloß wie eine Version aussieht
    2. vorhandener ZIP-Wert aus params-File, mit ${IMAGE_TAG}-Auflösung
    3. Fallback pro Server
    """
    raw_zip = strip_quotes(zip_name) if zip_name else ""
    env_zip = strip_quotes(env.get("ZIP", ""))
    env_dir = strip_quotes(env.get("DIR", ""))

    if raw_zip and not looks_like_plain_version(raw_zip):
        resolved_zip = resolve_image_tag_placeholders(raw_zip, version)
    elif env_zip and not looks_like_plain_version(env_zip):
        resolved_zip = resolve_image_tag_placeholders(env_zip, version)
    else:
        resolved_zip = default_zip_name(server, version)

    if env_dir:
        resolved_dir = resolve_image_tag_placeholders(env_dir, version)
    else:
        resolved_dir = default_dir_name(server, version)

    return resolved_zip, resolved_dir


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

    env = load_env_file(env_file)
    resolved_zip, resolved_dir = resolve_zip_and_dir(server, version, env, zip_name)

    upsert_env_value(env_file, "VERSION", version)
    upsert_env_value(env_file, "IMAGE_TAG", version)
    upsert_env_value(env_file, "FILE_ID", file_id)
    upsert_env_value(env_file, "ZIP", resolved_zip)
    upsert_env_value(env_file, "DIR", resolved_dir)

    update_image_tag(kust_file, version)

    print(f"Server '{server}' erfolgreich aktualisiert:")
    print(f"  - {env_file}")
    print(f"  - {kust_file}")
    print(f"  - IMAGE_TAG={version}")
    print(f"  - FILE_ID={file_id}")
    print(f"  - ZIP={resolved_zip}")
    print(f"  - DIR={resolved_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())