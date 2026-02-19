#!/bin/bash
# run this file in the current dir.
# or use bash to run it.


set -e
set -x

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# source env exported by env_init.sh
source $SCRIPT_DIR/.env

# get env
ENV_NAME="$ENV"
PROJECT_ROOT_DIR=$PROJECT_ROOT_LOCAL_DIR
CONF_SYNC_GIT_LOCAL_DIR=$CONF_SYNC_GIT_REPO_LOCAL_DIR
NGINX_TGT_DIR=$NGINX_SYSTEM_CONF_DIR

PROD_CONF_PROJECT_INSIDE_DIR="$PROJECT_ROOT_DIR/confgen/uni-conf/$ENV_NAME"

# prepare conf from another private repo: 
# 1. enter the private repo to fetch the latest conf 2. link it to the project inside
echo "pull the config file ${ENV_NAME}.py from ${PROD_CONF_REPO_DIR} git repo"
cd $CONF_SYNC_GIT_LOCAL_DIR
git pull
mkdir -p $PROD_CONF_PROJECT_INSIDE_DIR
ln -sn "$CONF_SYNC_GIT_LOCAL_DIR/${ENV_NAME}.py" "$PROD_CONF_PROJECT_INSIDE_DIR/conf.py" || true # skip set -x
# go to workdir
cd $PROJECT_ROOT_DIR
echo "now switch to release branch"
# 1. switch to release branch
git fetch origin --prune && git checkout release && git reset --hard origin/release
# 2. create venv
echo "create venv"
uv venv .venv --allow-existing --python 3.12
# 3. install dependency & install editable mode
echo "install dependency"
uv sync
uv pip install -e .
# 4. gen conf; link the nginx conf to the system nginx conf dir
echo "Generate conf for $ENV_NAME"
cd  "$PROJECT_ROOT_DIR/confgen"
uv run python gen.py -e $ENV_NAME
echo "Link nginx conf"
ln -sn "$PROJECT_ROOT_DIR/nginx/${ENV_NAME}.conf" "$NGINX_TGT_DIR/docgate.conf" || true
# 5. build vite
echo "Pnpm install & Vite build"
cd  "$PROJECT_ROOT_DIR/frontend"
pnpm i && pnpm run build

# 6. install gunicorn services for fastapi
echo "Install gunicorn for fastapi services"
sudo cp $SCRIPT_DIR/docgate-fastapi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable docgate-fastapi
sudo systemctl start docgate-fastapi

echo "done"