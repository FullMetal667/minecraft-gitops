from __future__ import annotations

import json
import zipfile
from pathlib import Path


def extract_modloader_id(zip_path: str | Path) -> str:
    zip_path = Path(zip_path)

    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP nicht gefunden: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        try:
            with zf.open("manifest.json") as f:
                manifest = json.load(f)
        except KeyError:
            raise RuntimeError("manifest.json fehlt im Modpack")

    minecraft = manifest.get("minecraft", {})
    modloaders = minecraft.get("modLoaders", [])

    if not modloaders:
        raise RuntimeError("Keine modLoaders gefunden")

    primary = next(
        (m for m in modloaders if m.get("primary")),
        modloaders[0],
    )

    return primary["id"]  # z.B. neoforge-21.1.117


def extract_modloader_parts(zip_path: str | Path) -> tuple[str, str]:
    loader = extract_modloader_id(zip_path)

    if "-" not in loader:
        return loader, ""

    name, version = loader.split("-", 1)
    return name, version