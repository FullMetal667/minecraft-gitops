#!/bin/bash
set -euxo pipefail

cd /data
cp /opt/.env /data/.env

if [[ -f .env ]]; then
  source .env
else
  echo "⚠️ .env nicht gefunden!"
  exit 1
fi

EULA_VAL="${EULA:-false}"
case "${EULA_VAL,,}" in
  true|yes|1)
    echo "eula=true" > eula.txt
    ;;
  *)
    echo "You must accept the EULA to install."
    exit 99
    ;;
esac

if [[ ! -f "$ZIP" ]]; then
    curl -fL -o "$ZIP" "$SERVER_FILE_URL"
    unzip -uo "$ZIP" -d .
fi

if [[ ! -f "libraries/net/minecraftforge/forge/${FORGE_VERSION}/unix_args.txt" ]]; then
    echo "Installing Forge server..."

    cp -r "./${DIR}/"* . || true

    if [[ -d "./${DIR}/world" ]] && [[ -z "$(ls -A ./world 2>/dev/null)" ]]; then
        mkdir -p ./world
        cp -a "./${DIR}/world/." ./world/
    fi

    java -jar "neoforge-${FORGE_VERSION}-installer.jar" --installServer

fi

# Stelle sicher, dass der mods-Ordner existiert
mkdir -p /data/mods

# SimpleBackups herunterladen (nur wenn nicht vorhanden)
if [[ ! -f /data/mods/simplebackups.jar ]]; then
  echo "⬇️ Lade SimpleBackups herunter..."
  curl -fL -o /data/mods/simplebackups.jar \
    https://mediafilez.forgecdn.net/files/6911/698/SimpleBackups-1.21-4.0.19.jar
fi

[[ -n "${MOTD:-}" ]] && sed -i "s/^motd=.*/motd=${MOTD}/" server.properties

[[ -n "${OPS:-}" ]] && echo "$OPS" | tr ',' '\n' > ops.txt
[[ -n "${ALLOWLIST:-}" ]] && echo "$ALLOWLIST" | tr ',' '\n' > white-list.txt

exec /data/startserver.sh
