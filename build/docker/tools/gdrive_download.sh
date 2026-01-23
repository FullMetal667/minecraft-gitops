#!/usr/bin/env bash
set -euo pipefail

ID="${1:?missing file id}"
OUT="${2:?missing output path}"

TMP="$(mktemp -d)"
COOKIE="${TMP}/cookie.txt"
HTML="${TMP}/page.html"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

cleanup() { rm -rf "${TMP}" >/dev/null 2>&1 || true; }
trap cleanup EXIT

is_zip() {
  [[ -f "$1" ]] || return 1
  # ZIP starts with "PK" => hex 50 4b
  [[ "$(head -c 2 "$1" | od -An -t x1 | tr -d ' \n')" == "504b" ]]
}

curl_fetch() {
  local url="$1" out="$2"
  curl -fL -A "${UA}" -c "${COOKIE}" -b "${COOKIE}" --retry 3 --retry-delay 2 \
    -o "${out}" "${url}"
}

# 0) Try direct "usercontent" download first (fast path)
DIRECT1="https://drive.usercontent.google.com/download?id=${ID}&export=download&confirm=t"
DIRECT2="https://drive.google.com/uc?export=download&id=${ID}&confirm=t"
DIRECT3="https://docs.google.com/uc?export=download&id=${ID}&confirm=t"

for U in "${DIRECT1}" "${DIRECT2}" "${DIRECT3}"; do
  rm -f "${OUT}.part" || true
  if curl_fetch "${U}" "${OUT}.part" >/dev/null 2>&1; then
    if is_zip "${OUT}.part"; then
      mv -f "${OUT}.part" "${OUT}"
      echo "[gdrive] OK direct download -> ${OUT}"
      exit 0
    fi
    # keep last html for parsing attempts
    cp -f "${OUT}.part" "${HTML}" || true
  fi
done

# 1) Fetch interstitial page (no confirm) and parse real download URL out of it
BASE="https://drive.google.com/uc?export=download&id=${ID}"
echo "[gdrive] fetching interstitial: ${BASE}"
curl_fetch "${BASE}" "${HTML}"

# 2) Newer interstitial pages often contain a direct drive.usercontent.google.com link
DL="$(grep -oE 'https://drive\.usercontent\.google\.com/download[^"'\'' <]+' "${HTML}" | head -n1 | sed 's/&amp;/\&/g' || true)"

if [[ -z "${DL}" ]]; then
  # fallback: sometimes confirm/uuid appear in HTML
  CONFIRM="$(sed -n 's/.*confirm=\([0-9A-Za-z_-]\+\).*/\1/p' "${HTML}" | head -n1 || true)"
  UUID="$(sed -n 's/.*uuid=\([0-9a-fA-F-]\+\).*/\1/p' "${HTML}" | head -n1 || true)"

  if [[ -n "${CONFIRM}" ]]; then
    DL="https://drive.usercontent.google.com/download?id=${ID}&export=download&confirm=${CONFIRM}"
    [[ -n "${UUID}" ]] && DL="${DL}&uuid=${UUID}"
  fi
fi

if [[ -z "${DL}" ]]; then
  echo "[gdrive] ERROR: Could not extract download URL."
  echo "[gdrive] First lines of response for debugging:"
  head -n 30 "${HTML}" || true
  exit 1
fi

echo "[gdrive] extracted download url: ${DL}"

# 3) Download with cookies
curl_fetch "${DL}" "${OUT}.part"

if ! is_zip "${OUT}.part"; then
  echo "[gdrive] ERROR: Downloaded content is not a zip (still HTML or blocked)."
  echo "[gdrive] Size: $(wc -c < "${OUT}.part" | tr -d ' ') bytes"
  echo "[gdrive] First lines:"
  head -n 30 "${OUT}.part" || true
  exit 1
fi

mv -f "${OUT}.part" "${OUT}"
echo "[gdrive] OK -> ${OUT}"
