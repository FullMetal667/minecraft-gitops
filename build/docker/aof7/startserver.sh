#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/aof7}"
DATA_DIR="${DATA_DIR:-/data}"
JAR="${JAR:-serverstarter-2.4.0.jar}"

# ---- RCON ---- (UNVERÄNDERT)
RCON_ENABLE="${RCON_ENABLE:-true}"
RCON_HOST="${RCON_HOST:-127.0.0.1}"
RCON_PORT="${RCON_PORT:-25575}"
RCON_PASSWORD="${RCON_PASSWORD:-mc321}"
RCON_WAIT_SECS="${RCON_WAIT_SECS:-1800}"   # bis zu 30 Minuten warten
RCON_POLL_INTERVAL="${RCON_POLL_INTERVAL:-5}"

# ---- Backup-Mod Auswahl ----
# advanced | none
BACKUP_MOD="${BACKUP_MOD:-advanced}"

# ---- Advanced Backups (Fabric) ----
AB_FILE_ID="${AB_FILE_ID:-4818556}"
AB_FILE_NAME="${AB_FILE_NAME:-AdvancedBackups-fabric-1.20-3.2.1.jar}"
AB_DIR1=$(( AB_FILE_ID / 1000 ))
AB_DIR2=$(( AB_FILE_ID % 1000 ))
ADVANCED_BACKUPS_URL="${ADVANCED_BACKUPS_URL:-https://mediafilez.forgecdn.net/files/${AB_DIR1}/${AB_DIR2}/${AB_FILE_NAME}}"

# ---- nc / ncat detection ---- (UNVERÄNDERT)
NC_BIN="${NC_BIN:-nc}"
if ! command -v "${NC_BIN}" >/dev/null 2>&1; then
  if command -v ncat >/dev/null 2>&1; then
    NC_BIN="ncat"
  fi
fi

mkdir -p "${DATA_DIR}/overrides/mods" "${DATA_DIR}/overrides/config" "${DATA_DIR}/mods" "${DATA_DIR}/config"

# =======================
# Config-Overrides anwenden (ohne Zwischenordner)
#   - Quelle:  ${DATA_DIR}/overrides/config/**  (PVC empfohlen)
#   - Ziel:    ${DATA_DIR}/config/**
#   - CONFIG_OVERRIDE_MODE:
#       force (default): immer überschreiben
#       fill: nur anlegen, wenn Ziel fehlt
# =======================
CONFIG_OVERRIDE_MODE="${CONFIG_OVERRIDE_MODE:-force}"
apply_config_overrides() {
  local base_src="${DATA_DIR}/overrides/config"
  local base_dst="${DATA_DIR}/config"
  [[ -d "${base_src}" ]] || return 0

  # Alle regulären Dateien aus base_src nach base_dst spiegeln
  while IFS= read -r -d '' src; do
    rel="${src#${base_src}/}"                    # relativer Pfad
    dst="${base_dst}/${rel}"
    mkdir -p "$(dirname "${dst}")"
    case "${CONFIG_OVERRIDE_MODE}" in
      force) cp -f "${src}" "${dst}" ;;
      fill)  [[ -f "${dst}" ]] || cp -f "${src}" "${dst}" ;;
      *)     cp -f "${src}" "${dst}" ;;          # Fallback
    esac
  done < <(find "${base_src}" -type f -print0)
}

# --- Helpers: AdvancedBackups Mod bereitstellen ---
selected_backup_filename() {
  case "${BACKUP_MOD}" in
    advanced) echo "${AB_FILE_NAME}" ;;
    none|"")  echo "" ;;
  esac
}
selected_backup_url() {
  case "${BACKUP_MOD}" in
    advanced) echo "${ADVANCED_BACKUPS_URL}" ;;
    none|"")  echo "" ;;
  esac
}

# nur in overrides/mods sicherstellen (Download oder Kopie), noch NICHT in mods kopieren
stage_backup_mod() {
  local fname url src=""
  fname="$(selected_backup_filename)"
  url="$(selected_backup_url)"
  [[ -n "${fname}" ]] || return 0

  if [[ -f "${DATA_DIR}/overrides/mods/${fname}" ]]; then
    return 0
  fi

  if [[ -f "${APP_DIR}/extras/${fname}" ]]; then
     src="${APP_DIR}/extras/${fname}"
  elif [[ -f "${DATA_DIR}/${fname}" ]]; then
     src="${DATA_DIR}/${fname}"
  fi

  if [[ -z "${src}" && -n "${url}" ]]; then
    echo "[BK] downloading ${fname} from ${url}"
    if ! curl -fsSL "${url}" -o "${DATA_DIR}/overrides/mods/${fname}"; then
      echo "[BK] WARN: download failed for ${fname} (continuing)"
      return 0
    fi
    return 0
  fi

  if [[ -n "${src}" ]]; then
    cp -f "${src}" "${DATA_DIR}/overrides/mods/${fname}" || true
  fi
}

# aus overrides (oder anderen Quellen) HART nach mods/ kopieren
place_backup_mod() {
  local fname src=""
  fname="$(selected_backup_filename)"
  [[ -n "${fname}" ]] || return 0

  if [[ -f "${DATA_DIR}/overrides/mods/${fname}" ]]; then
    src="${DATA_DIR}/overrides/mods/${fname}"
  elif [[ -f "${APP_DIR}/extras/${fname}" ]]; then
    src="${APP_DIR}/extras/${fname}"
  elif [[ -f "${DATA_DIR}/${fname}" ]]; then
    src="${DATA_DIR}/${fname}"
  fi

  if [[ -n "${src}" ]]; then
    mkdir -p "${DATA_DIR}/mods"
    cp -f "${src}" "${DATA_DIR}/mods/${fname}" || true
  fi
}

# =======================
# EULA (UNVERÄNDERT)
# =======================
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

# 1) ServerStarter JAR bereitstellen (UNVERÄNDERT)
cd "${DATA_DIR}"
if [[ ! -f "${JAR}" ]]; then
  echo "[SS] fetching ${JAR}"
  curl -fsSL -o "${JAR}" "https://github.com/TeamAOF/ServerStarter/releases/download/v2.4.0/${JAR}"
fi

# 2) Backup-Mod einmal in overrides/mods primen (falls noch nicht vorhanden)
SEL_FILE="$(selected_backup_filename)"
if [[ -n "${SEL_FILE}" && ! -f "${DATA_DIR}/overrides/mods/${SEL_FILE}" ]]; then
  stage_backup_mod || true
fi

# 3) ServerStarter starten (UNVERÄNDERT)
echo "[SS] starting ServerStarter ..."
java -jar "${JAR}" &
SERVER_PID=$!

# 4) Während des Install-/Sync-Fensters Backup-Mod in mods/ pinnen + Config-Overrides anwenden
(
  sleep 2
  end_time=$(( $(date +%s) + RCON_WAIT_SECS ))
  while [[ $(date +%s) -lt ${end_time} ]]; do
    place_backup_mod
    apply_config_overrides
    if command -v "${NC_BIN}" >/dev/null 2>&1 && ${NC_BIN} -z "${RCON_HOST}" "${RCON_PORT}" 2>/dev/null; then
      break
    fi
    sleep 2
  done
) &

# 5) Nach RCON-Start commands.txt schießen (UNVERÄNDERT)
if [[ "${RCON_ENABLE}" == "true" && -s "${DATA_DIR}/commands.txt" ]]; then
  echo "[RCON] waiting for ${RCON_HOST}:${RCON_PORT} (timeout ${RCON_WAIT_SECS}s) ..."
  waited=0
  until command -v "${NC_BIN}" >/dev/null 2>&1 && ${NC_BIN} -z "${RCON_HOST}" "${RCON_PORT}" 2>/dev/null; do
    sleep "${RCON_POLL_INTERVAL}"
    waited=$(( waited + RCON_POLL_INTERVAL ))
    if [[ "${waited}" -ge "${RCON_WAIT_SECS}" ]]; then
      echo "[RCON] timeout (${RCON_WAIT_SECS}s) – skip commands"
      break
    fi
  done

  if command -v "${NC_BIN}" >/dev/null 2>&1 && ${NC_BIN} -z "${RCON_HOST}" "${RCON_PORT}" 2>/dev/null; then
    sleep 3
    echo "[RCON] sending commands from commands.txt"
    sed -e 's#^/##' -e '/^\s*#/d' -e '/^\s*$/d' "${DATA_DIR}/commands.txt" | \
      /usr/local/bin/mcrcon -H "${RCON_HOST}" -P "${RCON_PORT}" -p "${RCON_PASSWORD}" -s || true
  fi
fi

# 6) Auf Server warten (UNVERÄNDERT)
wait "${SERVER_PID}"
