#!/usr/bin/env bash
set -euo pipefail

# Aufruf:
#   ./download_mce2_server.sh $FILE_ID "$ZIP"

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <CURSEFORGE_FILE_ID> <FILENAME.zip>"
  exit 1
fi

FILE_ID=$1
FILENAME=$2
ENV_FILE=".env"

DIR1=$(( FILE_ID / 1000 ))
DIR2=$(( FILE_ID % 1000 ))

FINAL_URL="https://mediafilez.forgecdn.net/files/${DIR1}/${DIR2}/${FILENAME}"

if ! curl --head --silent --fail "$FINAL_URL" > /dev/null; then
  echo "❌ Fehler: URL existiert nicht oder ist nicht erreichbar:"
  echo "   $FINAL_URL"
  exit 2
fi

if [[ -f "$ENV_FILE" ]]; then
  if grep -q '^SERVER_FILE_URL=' "$ENV_FILE"; then
    sed -i "s|^SERVER_FILE_URL=.*|SERVER_FILE_URL=$FINAL_URL|" "$ENV_FILE"
  else
    echo "SERVER_FILE_URL=$FINAL_URL" >> "$ENV_FILE"
  fi
else
  echo "SERVER_FILE_URL=$FINAL_URL" > "$ENV_FILE"
fi

echo "Neue‑URL:"
echo "   $FINAL_URL"
echo "→ gespeichert in $ENV_FILE"
