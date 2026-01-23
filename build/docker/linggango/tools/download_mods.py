import os, json, pathlib, requests, re
from urllib.parse import urlparse

API = "https://api.curseforge.com"
WEB_DL = "https://www.curseforge.com/api/v1/mods/1343057/files/7506380/download"

KEY = os.environ["CF_API_KEY"]
HEADERS = {"x-api-key": KEY, "accept": "application/json"}

mods_dir = pathlib.Path(os.environ.get("APP_DIR", "/data/forge")) / "mods"
mods_dir.mkdir(parents=True, exist_ok=True)

def filename_from_response(resp: requests.Response) -> str:
    cd = resp.headers.get("content-disposition", "")
    m = re.search(r'filename="?([^"]+)"?', cd)
    if m:
        return m.group(1)
    # fallback: take last segment of final redirected URL
    return pathlib.Path(urlparse(resp.url).path).name

def download_stream(url: str, out_dir: pathlib.Path) -> pathlib.Path:
    with requests.get(url, allow_redirects=True, stream=True, timeout=300) as resp:
        resp.raise_for_status()
        fname = filename_from_response(resp)
        out = out_dir / fname
        if out.exists():
            print("OK (exists):", fname)
            return out

        print("Downloading:", fname)
        with open(out, "wb") as w:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    w.write(chunk)
        return out

manifest_path = os.environ.get("MANIFEST_PATH", "/work/modpack/manifest.json")

with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = json.load(f)

for entry in manifest.get("files", []):
    pid = entry["projectID"]
    fid = entry["fileID"]

    # Try Core API first
    r = requests.get(f"{API}/v1/mods/{pid}/files/{fid}", headers=HEADERS, timeout=60)

    if r.status_code == 200:
        data = r.json()["data"]
        url = data.get("downloadUrl")
        if not url:
            # Rare, but fallback to web endpoint
            url = WEB_DL.format(pid=pid, fid=fid)
        download_stream(url, mods_dir)
        continue

    if r.status_code == 403:
        # Fallback without API/slug
        url = WEB_DL.format(pid=pid, fid=fid)
        download_stream(url, mods_dir)
        continue

    # other errors should fail loudly
    r.raise_for_status()

print("Done.")

