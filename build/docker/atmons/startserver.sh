#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# Basis-Dirs
# -----------------------------
APP_DIR="${APP_DIR:-/opt/atm10}"
DATA_DIR="${DATA_DIR:-/data}"

cd "${DATA_DIR}"

# -----------------------------
# ATM10 / NeoForge Settings
# -----------------------------
NEOFORGE_VERSION="${NEOFORGE_VERSION:-21.1.214}"

# Java-Auswahl: wie ATM10_JAVA im .bat
ATM10_JAVA="${ATM10_JAVA:-java}"

# Restartverhalten / Install-only
ATM10_RESTART="${ATM10_RESTART:-true}"
ATM10_INSTALL_ONLY="${ATM10_INSTALL_ONLY:-false}"

INSTALLER="${INSTALLER:-${DATA_DIR}/neoforge-${NEOFORGE_VERSION}-installer.jar}"
NEOFORGE_URL="${NEOFORGE_URL:-https://maven.neoforged.net/releases/net/neoforged/neoforge/${NEOFORGE_VERSION}/neoforge-${NEOFORGE_VERSION}-installer.jar}"

# Standard-Args-Datei von NeoForge (Unix)
ATM10_ARGS_FILE_DEFAULT="libraries/net/neoforged/neoforge/${NEOFORGE_VERSION}/unix_args.txt"
ATM10_ARGS_FILE="${ATM10_ARGS_FILE:-${ATM10_ARGS_FILE_DEFAULT}}"

# -----------------------------
# RCON Settings (wie bei AOF7)
# -----------------------------
RCON_ENABLE="${RCON_ENABLE:-true}"
RCON_HOST="${RCON_HOST:-127.0.0.1}"
RCON_PORT="${RCON_PORT:-25575}"
RCON_PASSWORD="${RCON_PASSWORD:-mc321}"
RCON_WAIT_SECS="${RCON_WAIT_SECS:-1800}"
RCON_POLL_INTERVAL="${RCON_POLL_INTERVAL:-5}"

# -----------------------------
# Backup-Mod Auswahl
# -----------------------------
# BACKUP_MOD=advanced | none
BACKUP_MOD="${BACKUP_MOD:-advanced}"

# AdvancedBackups Defaults (kannst du bei Bedarf atm10-spezifisch anpassen)
AB_FILE_ID="${AB_FILE_ID:-4818556}"
AB_FILE_NAME="${AB_FILE_NAME:-AdvancedBackups-fabric-1.20-3.2.1.jar}"
AB_DIR1=$(( AB_FILE_ID / 1000 ))
AB_DIR2=$(( AB_FILE_ID % 1000 ))
ADVANCED_BACKUPS_URL="${ADVANCED_BACKUPS_URL:-https://mediafilez.forgecdn.net/files/${AB_DIR1}/${AB_DIR2}/${AB_FILE_NAME}}"

# -----------------------------
# nc / ncat detection
# -----------------------------
NC_BIN="${NC_BIN:-nc}"
if ! command -v "${NC_BIN}" >/dev/null 2>&1; then
  if command -v ncat >/dev/null 2>&1; then
    NC_BIN="ncat"
  fi
fi

mkdir -p "${DATA_DIR}/overrides/mods" "${DATA_DIR}/overrides/config" "${DATA_DIR}/mods" "${DATA_DIR}/config"

# =======================
# Config-Overrides anwenden
# =======================
CONFIG_OVERRIDE_MODE="${CONFIG_OVERRIDE_MODE:-force}"
apply_config_overrides() {
  local base_src="${DATA_DIR}/overrides/config"
  local base_dst="${DATA_DIR}/config"
  [[ -d "${base_src}" ]] || return 0

  while IFS= read -r -d '' src; do
    rel="${src#${base_src}/}"
    dst="${base_dst}/${rel}"
    mkdir -p "$(dirname "${dst}")"
    case "${CONFIG_OVERRIDE_MODE}" in
      force) cp -f "${src}" "${dst}" ;;
      fill)  [[ -f "${dst}" ]] || cp -f "${src}" "${dst}" ;;
      *)     cp -f "${src}" "${dst}" ;;
    esac
  done < <(find "${base_src}" -type f -print0)
}

# =======================
# AdvancedBackups helper
# =======================
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

# Nur nach overrides/mods primen
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

# Aus overrides nach mods kopieren
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
# Java-Check (>= 21)
# =======================
if ! command -v "${ATM10_JAVA}" >/dev/null 2>&1; then
  echo "[ATM10] Java nicht gefunden (ATM10_JAVA=${ATM10_JAVA})"
  exit 1
fi

JAVA_VERSION_OUT="$("${ATM10_JAVA}" -version 2>&1 | head -n1)"
JAVA_MAJOR=0
if [[ "${JAVA_VERSION_OUT}" =~ \"([0-9]+)\. ]]; then
  JAVA_MAJOR="${BASH_REMATCH[1]}"
fi

if (( JAVA_MAJOR < 21 )); then
  echo "[ATM10] Minecraft 1.21 benötigt Java 21 – gefunden: ${JAVA_VERSION_OUT}"
  exit 1
fi

# =======================
# EULA
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

# =======================
# server.properties Default
# =======================
if [[ ! -f server.properties ]]; then
  MOTD_VAL="${MOTD:-All the Mods 10}"
  {
    echo "allow-flight=true"
    echo "motd=${MOTD_VAL}"
    echo "max-tick-time=180000"
  } > server.properties
  echo "[ATM10] Default server.properties geschrieben"
fi

# =======================
# NeoForge installieren
# =======================
install_neoforge() {
  if [[ -f "${ATM10_ARGS_FILE}" ]]; then
    echo "[ATM10] NeoForge bereits installiert (Args-Datei gefunden: ${ATM10_ARGS_FILE})"
    return 0
  fi

  echo "[ATM10] NeoForge nicht installiert, starte Installation für ${NEOFORGE_VERSION}"

  if [[ ! -f "${INSTALLER}" ]]; then
    echo "[ATM10] Lade Installer von ${NEOFORGE_URL}"
    curl -fsSL -o "${INSTALLER}" "${NEOFORGE_URL}"
  fi

  "${ATM10_JAVA}" -jar "${INSTALLER}" -installServer
}

install_neoforge

if [[ "${ATM10_INSTALL_ONLY}" == "true" ]]; then
  echo "[ATM10] INSTALL_ONLY=true – Installation abgeschlossen, beende."
  exit 0
fi

# 2) Backup-Mod primen
SEL_FILE="$(selected_backup_filename)"
if [[ -n "${SEL_FILE}" && ! -f "${DATA_DIR}/overrides/mods/${SEL_FILE}" ]]; then
  stage_backup_mod || true
fi

# =======================
# Serverstart + RCON/Overrides
# =======================
start_server() {
  echo "[ATM10] Starte NeoForge Server mit:"
  echo "  ${ATM10_JAVA} @user_jvm_args.txt @${ATM10_ARGS_FILE} nogui"
  "${ATM10_JAVA}" @user_jvm_args.txt @"${ATM10_ARGS_FILE}" nogui &
  SERVER_PID=$!
}

# einmal starten (kein Restart-Loop, kann man später einbauen)
start_server

# Overrides + Backup-Mod während des Startfensters anwenden
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

# RCON-Commands aus commands.txt schicken
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

# Auf Server warten
wait "${SERVER_PID}"

