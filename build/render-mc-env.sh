#!/usr/bin/env bash
set -euo pipefail

PARAM_FILE="${1:?missing param file}"
OUT_FILE="${2:?missing output file}"

set -a
source "$PARAM_FILE"
set +a

cat > "$OUT_FILE" <<EOF
# GENERATED FILE - DO NOT EDIT
MOD_VERSION=${IMAGE_TAG}
FILE_ID=${FILE_ID}
ZIP=${ZIP}
DIR=${DIR}
MOTD=All the Mods 10 (${IMAGE_TAG}) on OpenShift
EULA=true
MOD_NAME=${MOD_NAME}
NAMESPACE=minecraft-${MOD_NAME}
EOF