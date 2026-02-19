#!/bin/bash
# This is used to install the dependency to the machine.
# It should be run only once in the machine

# install uv for python (only if not installed)
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    wget -qO- https://astral.sh/uv/install.sh | sh
else
    echo "uv already installed. Skipping."
fi

# install volta (only if not installed)
if ! command -v volta &> /dev/null; then
    echo "Installing Volta..."
    curl https://get.volta.sh | bash
else
    echo "Volta already installed. Skipping."
fi

# install pnpm (only if not installed)
if ! command -v pnpm &> /dev/null; then
    echo "Installing pnpm..."
    wget -qO- https://get.pnpm.io/install.sh | sh -
else
    echo "pnpm already installed. Skipping."
fi

# install git (only if not installed)
if ! command -v git &> /dev/null; then
    echo "Installing Git..."
    sudo apt install -y git
else
    echo "Git already installed. Skipping."
fi

# we assume 
# 1. nginx has already been installed
# 2. private repo that contains config file (used for `confgen/gen.py`) has already been cloned.
# Then **fill/change** the following ENV vars so we can then run the `project_init.sh`

cat > .env << 'EOF'

ENV=prod
PROJECT_ROOT_LOCAL_DIR=/root/deploy/dajuan-english/docgate
CONF_SYNC_GIT_REPO_LOCAL_DIR=/root/github/private-conf/web/docgate/confgen
NGINX_SYSTEM_CONF_DIR=/etc/nginx/sites-enabled

EOF

