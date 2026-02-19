#!/bin/bash
# This is used to install the dependency to the machine.
# It should be run only once in the machine

# install uv for python
wget -qO- https://astral.sh/uv/install.sh | sh

# install volta, pnpm for vite build
curl https://get.volta.sh | bash
wget -qO- https://get.pnpm.io/install.sh | sh -

sudo apt install -y git

# we assume 
# 1. nginx has already been installed
# 2. private repo that contains config file (used for `confgen/gen.py`) has already been cloned.
# Then **fill/change** the following ENV vars so we can then run the `project_init.sh`

cat > .env << 'EOF'

ENV=prod
PROJECT_ROOT_LOCAL_DIR=/root/deploy/dajuan-english/docgate
PROD_CONF_SYNC_GIT_REPO_LOCAL_DIR=/root/github/private-conf
PROD_CONF_SYNC_REL_PATH=web/docgate/confgen
NGINX_SYSTEM_CONF_DIR=/etc/nginx/sites-enabled

EOF

