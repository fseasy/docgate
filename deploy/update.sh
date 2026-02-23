#!/bin/bash
set -Eeuo pipefail
trap 'echo "❌ Error at line $LINENO: $BASH_COMMAND"; exit 1' ERR
set -x

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# source env exported by env_init.sh
source $SCRIPT_DIR/.env

# the update conf/dependency/vite logic are the same as project-init
# 1. pull the latest code 2. gen conf 3. vite build 4. restart systemd gunicorn fastapi
# the gunicorn service has already been restarted!
$SCRIPT_DIR/project_init.sh || exit 1

# restart nginx
nginx -t
systemctl restart nginx
