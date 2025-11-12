#!/usr/bin/env bash
set -Eeuo pipefail

DATA="/data"
SEED="/opt/aof7"
JAR_OPT="/opt/serverstarter-2.4.0.jar"
JAR_DATA="${DATA}/serverstarter-2.4.0.jar"
RAMDISK_PATH="${RAMDISK_PATH:-}"   # optional via Deployment setzen, z.B. /ramdisk
RAMDISK_SIZE="${RAMDISK_SIZE:-2G}" # nur Info/Log

umask 0002

# 1) Erst-Start: /data seeden, falls noch leer
if [ ! -f "${DATA}/server-setup-config.yaml" ]; then
  echo "First run: seeding ${DATA} from ${SEED}"
  cp -a "${SEED}/." "${DATA}/"
fi

# 2) Verzeichnisstruktur + Rechte (OpenShift: arbitrary UID)
mkdir -p "${DATA}/logs" "${DATA}/config"
# Offen, aber robust. Optional enger machen, wenn fsGroup funktioniert.
find "${DATA}" -type d -exec chmod 0777 {} + || true
find "${DATA}" -type f -exec chmod 0666 {} + || true

# 3) Optional RAM-"Disk": nur wenn Deployment einen Memory-EmptyDir mounted hat
#    (z.B. mountPath: /ramdisk). Kein 'mount' im Container!
DO_RAMDISK=0
if grep -Eq '^[[:space:]]*ramDisk:[[:space:]]*yes' "${DATA}/server-setup-config.yaml"; then
  if [ -n "${RAMDISK_PATH}" ] && [ -d "${RAMDISK_PATH}" ]; then
    SAVE_DIR="$(awk -F= '/^level-name=/{print $2}' "${DATA}/server.properties" || true)"
    SAVE_DIR="${SAVE_DIR:-world}"
    echo "RAM mode requested; using ${RAMDISK_PATH} for world '${SAVE_DIR}'"
    mkdir -p "${RAMDISK_PATH}/${SAVE_DIR}"
    # Falls schon eine Welt existiert, initial kopieren
    if [ -d "${DATA}/${SAVE_DIR}" ]; then
      cp -a "${DATA}/${SAVE_DIR}/." "${RAMDISK_PATH}/${SAVE_DIR}/" || true
    fi
    # Symlink Welt -> RAM
    rm -rf "${DATA:?}/${SAVE_DIR}" && ln -s "${RAMDISK_PATH}/${SAVE_DIR}" "${DATA}/${SAVE_DIR}"
    DO_RAMDISK=1
  else
    echo "ramDisk: yes konfiguriert, aber RAMDISK_PATH ist nicht gemountet. Weiter ohne RAM."
  fi
fi

# 4) ServerStarter JAR wählen/holen
if [ -f "${JAR_DATA}" ]; then
  JAR="${JAR_DATA}"
elif [ -f "${JAR_OPT}" ]; then
  JAR="${JAR_OPT}"
else
  # Fallback: herunterladen (Cluster muss Egress erlauben)
  URL="https://github.com/TeamAOF/ServerStarter/releases/download/v2.4.0/serverstarter-2.4.0.jar"
  echo "serverstarter.jar not found; downloading ${URL}"
  curl -fL -A "Mozilla/5.0" -o "${JAR_DATA}" "${URL}"
  JAR="${JAR_DATA}"
fi

# 5) Start (arbeite aus /data, damit relative Pfade passen)
cd "${DATA}"

{
  echo "# You accepted the EULA by deploying this server"
  date -u +"# %Y-%m-%dT%H:%M:%SZ"
  echo "eula=true"
} > eula.txt

if [ ! -f eula.txt ] || ! grep -q 'eula=true' eula.txt; then
  if [ "${EULA:-}" = "TRUE" ] || [ "${EULA:-}" = "true" ]; then
    {
      echo "# By changing the setting below to TRUE you are indicating your agreement to the EULA (https://aka.ms/MinecraftEULA)."
      echo "# $(date -u)"
      echo "eula=true"
    } > eula.txt
    echo "[init] EULA accepted via ENV"
  else
    echo "[init] EULA not accepted. Setze ENV EULA=true oder lege /data/eula.txt mit 'eula=true' an."
    exit 3
  fi
fi

echo "Launching ServerStarter with config ${DATA}/server-setup-config.yaml"
exec java -jar "${JAR}" --config "${DATA}/server-setup-config.yaml"

