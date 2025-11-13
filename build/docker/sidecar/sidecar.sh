#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${DATA_DIR:-/data}"
LOG_DIR="$DATA_DIR/logs"
LOGFILE="$LOG_DIR/latest.log"
MODS_DIR="$DATA_DIR/mods"
CMDS_FILE="${CMDS_FILE:-$DATA_DIR/commands.txt}"
LOCK_DIR="$DATA_DIR/.ops"
LOCK_FILE="$LOCK_DIR/first-boot-done"
BACKUP_URL="${BACKUP_URL:-https://mediafilez.forgecdn.net/files/${DIR1}/${DIR2}/${SB_FILE_NAME}}"              # direkte Datei-URL (CDN) hier setzen
BACKUP_JAR_NAME="${BACKUP_JAR_NAME:-SimpleBackups-1.20.1-3.1.18.jar}"    # z.B. simplebackup-2.0-1.20.jar / textile_backup-3.0.0-1.20.jar

mkdir -p "$LOCK_DIR" "$MODS_DIR"

echo "[sidecar] Warte auf Server-Logverzeichnis ..."
until [ -d "$LOG_DIR" ]; do sleep 2; done

echo "[sidecar] Warte auf Logdatei $LOGFILE ..."
until [ -f "$LOGFILE" ]; do sleep 2; done

# === Warte bis RCON-Port offen ist ===
SERVER_PROPS="$DATA_DIR/server.properties"
echo "[sidecar] Warte auf server.properties ..."
until [ -f "$SERVER_PROPS" ]; do sleep 1; done

RCON_HOST="${RCON_HOST:-127.0.0.1}"
RCON_PORT="$(awk -F= '/^rcon.port=/{print $2}' "$SERVER_PROPS" || true)"
RCON_PASS="$(awk -F= '/^rcon.password=/{print $2}' "$SERVER_PROPS" || true)"

if [[ -z "$RCON_PORT" || -z "$RCON_PASS" ]]; then
  echo "[sidecar][FATAL] RCON ist nicht sauber konfiguriert (rcon.port / rcon.password)."
  echo "[sidecar] Breche ab."
  sleep infinity
fi

echo "[sidecar] Warte bis RCON auf $RCON_HOST:$RCON_PORT erreichbar ist ..."
until nc -z "$RCON_HOST" "$RCON_PORT"; do sleep 1; done
echo "[sidecar] RCON erreichbar."

# === Backup-Mod (nur wenn nicht vorhanden) ===
if ! ls "$MODS_DIR"/simplebackup-*.jar "$MODS_DIR"/textile_backup-*.jar >/dev/null 2>&1; then
  if [[ -n "$BACKUP_URL" && -n "$BACKUP_JAR_NAME" ]]; then
    echo "[sidecar] Lade Backup-Mod: $BACKUP_JAR_NAME"
    curl -fL "$BACKUP_URL" -o "$MODS_DIR/$BACKUP_JAR_NAME"
    # perms für OpenShift
    chgrp -R 0 "$MODS_DIR" && chmod -R g+rwX "$MODS_DIR" || true
    echo "[sidecar] Backup-Mod abgelegt. (Wirksam nach dem nächsten Server-Restart.)"
  else
    echo "[sidecar][WARN] BACKUP_URL/BACKUP_JAR_NAME nicht gesetzt – überspringe Mod-Download."
  fi
else
  echo "[sidecar] Backup-Mod bereits vorhanden – überspringe Download."
fi

# === RCON-Commands NUR EINMAL je Welt/Server ===
if [[ -f "$CMDS_FILE" && ! -f "$LOCK_FILE" ]]; then
  echo "[sidecar] Sende RCON-Kommandos aus $CMDS_FILE ..."
  # führende "/" entfernen – RCON erwartet Befehle ohne Slash
  sed -e 's|^/||' "$CMDS_FILE" | /usr/local/bin/mcrcon -H "$RCON_HOST" -P "$RCON_PORT" -p "$RCON_PASS" -t || true
  date > "$LOCK_FILE"
  chgrp 0 "$LOCK_FILE" && chmod g+rw "$LOCK_FILE" || true
  echo "[sidecar] RCON-Kommandos gesendet (Lock: $LOCK_FILE)."
else
  if [[ -f "$LOCK_FILE" ]]; then
    echo "[sidecar] RCON-Kommandos wurden bereits ausgeführt – überspringe."
  else
    echo "[sidecar][WARN] $CMDS_FILE nicht gefunden – überspringe RCON-Kommandos."
  fi
fi

echo "[sidecar] Fertig. Lege mich schlafen."
sleep infinity

