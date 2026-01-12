import os, json, pathlib, requests

API = "https://api.curseforge.com"
key = os.environ["CF_API_KEY"]

mods_dir = pathlib.Path("/srv/mc/mods")
mods_dir.mkdir(parents=True, exist_ok=True)

with open("/work/modpack/manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

headers = {"x-api-key": key}

for entry in manifest.get("files", []):
    pid = entry["projectID"]
    fid = entry["fileID"]

    r = requests.get(f"{API}/v1/mods/{pid}/files/{fid}", headers=headers, timeout=60)
    r.raise_for_status()
    data = r.json()["data"]
    url = data.get("downloadUrl")
    name = data.get("fileName")

    if not url or not name:
        raise RuntimeError(f"Missing downloadUrl/fileName for project={pid} file={fid}")

    out = mods_dir / name
    if out.exists():
        print("exists:", name)
        continue

    print("download:", name)
    with requests.get(url, stream=True, timeout=300) as dl:
        dl.raise_for_status()
        with open(out, "wb") as w:
            for chunk in dl.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    w.write(chunk)

print("done")

