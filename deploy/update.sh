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

# the update conf/dependency/vite logic are the same as project-init
./project_init.sh

# run server

