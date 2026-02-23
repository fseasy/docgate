#!/bin/bash
# This script can be run in once the `env_init.sh` has been called and the dependency dir is prepared already
# it's also intended for update project (pull latest & re-build & reload)

set -Eeuo pipefail
trap 'echo "❌ Error at line $LINENO: $BASH_COMMAND"; exit 1' ERR
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


PROD_CONF_PROJECT_INSIDE_DIR="$PROJECT_ROOT_LOCAL_DIR/confgen/uni-conf/$ENV"

# prepare conf from another private repo: 
# 1. enter the private repo to fetch the latest conf 2. link it to the project inside
echo "pull the config file ${ENV}.py from ${CONF_SYNC_GIT_REPO_LOCAL_DIR} git repo"
cd $CONF_SYNC_GIT_REPO_LOCAL_DIR
git pull
mkdir -p $PROD_CONF_PROJECT_INSIDE_DIR
ln -sn "$CONF_SYNC_GIT_REPO_LOCAL_DIR/${ENV}.py" "$PROD_CONF_PROJECT_INSIDE_DIR/conf.py" || true # skip set -x
# go to workdir
cd $PROJECT_ROOT_LOCAL_DIR
echo "now switch to release branch"
# 1. switch to release branch
git fetch origin --prune
git checkout release
git reset --hard origin/release
# 2. create venv
echo "create venv"
uv venv .venv --allow-existing --python 3.12
# 3. install dependency & install editable mode
echo "install dependency"
uv sync
uv pip install -e .
# 4. gen conf; link the nginx conf to the system nginx conf dir
echo "Generate conf for $ENV"
cd  "$PROJECT_ROOT_LOCAL_DIR/confgen"
uv run python gen.py -e $ENV
echo "Link nginx conf"
ln -sn "$PROJECT_ROOT_LOCAL_DIR/nginx/${ENV}.conf" "$NGINX_SYSTEM_CONF_DIR/docgate.conf" || true
# 5. build vite
echo "Pnpm install & Vite build"
cd  "$PROJECT_ROOT_LOCAL_DIR/frontend"
pnpm i
pnpm run build

# 6. install gunicorn services for fastapi

service_fname="$SYSTEMD_SERVICE_NAME.service"
service_target_fpath="/etc/systemd/system/$service_fname"
service_source_fpath="$SCRIPT_DIR/$service_fname"

if [ ! -f "$service_target_fpath" ]; then
  echo "Install gunicorn for fastapi services"
  sudo cp $service_source_fpath $service_target_fpath
  sudo systemctl daemon-reload
  sudo systemctl enable $SYSTEMD_SERVICE_NAME
  sudo systemctl start $SYSTEMD_SERVICE_NAME
else
  echo "Update gunicorn fastapi services"
  sudo cp $service_source_fpath $service_target_fpath
  sudo systemctl daemon-reload
  sudo systemctl enable $SYSTEMD_SERVICE_NAME
  sudo systemctl restart $SYSTEMD_SERVICE_NAME
fi

echo "Test Nginx config & Restart Nginx"
# restart nginx
nginx -t
systemctl restart nginx

echo "All done"