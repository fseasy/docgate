#!/bin/bash

# get env
ENV_NAME="$ENV"
PROJECT_ROOT_DIR=$PROJECT_ROOT_LOCAL_DIR
PROD_CONF_REPO_DIR=$PROD_CONF_SYNC_GIT_REPO_LOCAL_DIR
PROD_CONF_ORIGIN_PATH=$PROD_CONF_SYNC_REL_PATH
REPO_PATH=$REPO_SSH_PATH
NGINX_TGT_DIR=$NGINX_SYSTEM_CONF_DIR

PROD_CONF_PROJECT_INSIDE_DIR="$PROJECT_ROOT_DIR/confgen/uni-conf/$ENV_NAME"

# clone
echo "CLONE repo to [$PROJECT_ROOT_DIR]"
git clone $REPO_PATH $PROJECT_ROOT_DIR
# prepare conf from another private repo: 
# 1. enter the private repo to fetch the latest conf 2. link it to the project inside
echo "pull the config file ${ENV_NAME}.py from ${PROD_CONF_REPO_DIR} git repo"
cd $PROD_CONF_REPO_DIR
git pull
mkdir -p $PROD_CONF_PROJECT_INSIDE_DIR
ln -s "$PROD_CONF_REPO_DIR/$PROD_CONF_ORIGIN_PATH" "$PROD_CONF_PROJECT_INSIDE_DIR/conf.py"
# go to workdir
cd $PROJECT_ROOT_DIR
echo "now switch to release branch"
# 1. switch to release branch
git checkout release
# 2. create venv
echo "create venv"
uv venv --python 3.12
# 3. install dependency & install editable mode
echo "install dependency"
uv sync
uv pip install -e .
# 4. gen conf; link the nginx conf to the system nginx conf dir
echo "Generate conf for $ENV_NAME"
cd confgen
uv run python gen.py -e $ENV_NAME
echo "Link nginx conf"
ln -s "$NGINX_TGT_DIR/docgate.conf" "$PROJECT_ROOT_DIR/nginx/${ENV_NAME}.conf"
echo "done"