#!/bin/bash
set -e
set -x

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# source env exported by env_init.sh
source $SCRIPT_DIR/.env

# check env
: "${ENV?env-var ENV is required}"
: "${PROJECT_ROOT_LOCAL_DIR?env-var PROJECT_ROOT_LOCAL_DIR is required}"
: "${CONF_SYNC_GIT_REPO_LOCAL_DIR?env-var CONF_SYNC_GIT_REPO_LOCAL_DIR is required}"
: "${NGINX_SYSTEM_CONF_DIR?env-var NGINX_SYSTEM_CONF_DIR is required}"
: "${SYSTEMD_SERVICE_NAME?env-var SYSTEMD_SERVICE_NAME is required}"


PROD_CONF_PROJECT_INSIDE_DIR="$PROJECT_ROOT_DIR/confgen/uni-conf/$ENV_NAME"

# the update conf/dependency/vite logic are the same as project-init
# 1. pull the latest code 2. gen conf 3. vite build 4. restart systemd gunicorn fastapi
# the gunicorn service has already been restarted!
$SCRIPT_DIR/project_init.sh

# restart nginx
nginx -t
systemctl restart nginx
