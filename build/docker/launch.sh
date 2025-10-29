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

EULA_VAL="${EULA:-false}"
case "${EULA_VAL,,}" in
  true|yes|1) echo "eula=true" > eula.txt ;;
  *) echo "You must accept the EULA to install."; exit 99 ;;
esac

if [[ ! -f "${ZIP:?ZIP not set}" ]]; then
  if [[ -z "${SERVER_FILE_URL:-}" ]]; then
    : "${FILE_ID:?FILE_ID not set}"
    DIR1=$(( FILE_ID / 1000 ))
    DIR2=$(( FILE_ID % 1000 ))
    SERVER_FILE_URL="https://mediafilez.forgecdn.net/files/${DIR1}/${DIR2}/${ZIP}"
  fi
  echo "Downloading ${ZIP} from ${SERVER_FILE_URL}"
  curl -fL -o "$ZIP" "$SERVER_FILE_URL"
fi

unzip -uo "$ZIP" -d .

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

SP="/data/server.properties"
DEFAULT_SP="/opt/defaults/server.properties"

# 1) Vorlage einmalig auf PVC kopieren (falls noch nicht vorhanden)
if [[ ! -f "$SP" ]]; then
  if [[ -f "$DEFAULT_SP" ]]; then
    cp -f "$DEFAULT_SP" "$SP"
  else
    printf "allow-flight=true\nwhite-list=true\nmax-tick-time=180000\nmotd=All the Mods 10\n" > "$SP"
  fi
fi

# 2) Schreibrechte für Gruppe geben (fsGroup hat Group-Ownership)
chmod g+rw "$SP" || true
# optional: gesamten Ordner gruppenschreibbar machen
chmod -R g+rwX /data || true

# 3) MOTD setzen – ohne -i (aber auf die PVC-Datei, nicht die CM)
if [[ -n "${MOTD:-}" ]]; then
  tmp="$(mktemp)"
  awk -v m="$MOTD" '
    BEGIN{set=0}
    /^motd=/{print "motd=" m; set=1; next}
    {print}
    END{if(!set) print "motd=" m}
  ' "$SP" > "$tmp" && mv "$tmp" "$SP"
fi

[[ -n "${MOTD:-}" ]] && sed -i "s/^motd=.*/motd=${MOTD}/" server.properties

[[ -n "${OPS:-}" ]] && echo "$OPS" | tr ',' '\n' > ops.txt
[[ -n "${ALLOWLIST:-}" ]] && echo "$ALLOWLIST" | tr ',' '\n' > white-list.txt

exec /data/startserver.sh
