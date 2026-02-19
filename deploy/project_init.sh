#!/bin/bash
set -e
set -x

source .env

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
git fetch
git checkout release
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
ln -sn "$NGINX_TGT_DIR/docgate.conf" "$PROJECT_ROOT_DIR/nginx/${ENV_NAME}.conf" || true
# 5. build vite
echo "Vite build"
cd  "$PROJECT_ROOT_DIR/frontend"
pnpm run build
echo "done"