#!/bin/sh
set -eu

export HOME=${HOME:-/tmp}

git config --global --add safe.directory /opt/minecraft-gitops || true

exec "$@"