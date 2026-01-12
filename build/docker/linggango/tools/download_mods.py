import os, json, pathlib, requests, re
from urllib.parse import urlparse

API = "https://api.curseforge.com"
KEY = os.environ["CF_API_KEY"]
HEADERS = {"x-api-key": KEY, "accept": "application/json"}

mods_dir = pathlib.Path("/srv/mc/mods")
mods_dir.mkdir(parents=True, exist_ok=True)

def get_slug(project_id: int) -> str:
    r = requests.get(f"{API}/v1/mods/{project_id}", headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.json()["data"]["slug"]

def download_via_web(slug: str, file_id: int) -> pathlib.Path:
    # offizieller Download-Redirect der Website
    dl = f"https://www.curseforge.com/minecraft/mc-mods/{slug}/files/{file_id}/download"
    with requests.get(dl, allow_redirects=True, stream=True, timeout=300) as resp:
        resp.raise_for_status()

        # Dateiname aus Content-Disposition oder aus URL
        fname = None
        cd = resp.headers.get("content-disposition", "")
        m = re.search(r'filename="?([^"]+)"?', cd)
        if m:
            fname = m.group(1)
        if not fname:
            fname = pathlib.Path(urlparse(resp.url).path).name

        out = mods_dir / fname
        if out.exists():
            print("OK (exists):", fname)
            return out

        print("Downloading (web):", fname)
        with open(out, "wb") as w:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    w.write(chunk)
        return out

with open("/work/modpack/manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

for entry in manifest.get("files", []):
    pid = entry["projectID"]
    fid = entry["fileID"]

    r = requests.get(f"{API}/v1/mods/{pid}/files/{fid}", headers=HEADERS, timeout=60)
    if r.status_code == 403:
        slug = get_slug(pid)
        download_via_web(slug, fid)
        continue

    r.raise_for_status()
    data = r.json()["data"]
    url = data["downloadUrl"]
    name = data["fileName"]

    out = mods_dir / name
    if out.exists():
        print("OK (exists):", name)
        continue

    print("Downloading (api):", name)
    with requests.get(url, stream=True, timeout=300) as dl:
        dl.raise_for_status()
        with open(out, "wb") as w:
            for chunk in dl.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    w.write(chunk)

print("Done.")

