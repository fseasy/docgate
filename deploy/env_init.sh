#!/bin/bash
# This is used to install the dependency to the machine.
# It should be run only once in the machine
# run this file in the current dir.
# or use bash to run it.

# we assume
# 1. nginx has already been installed
# 2. private repo that contains config file (used for `confgen/gen.py`) has already been cloned.
# Then **fill/change** the following ENV vars so we can then run the `project_init.sh`

set -Eeuo pipefail
trap 'echo "❌ Error at line $LINENO: $BASH_COMMAND"; exit 1' ERR
# set -x

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT_LOCAL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# for ssh-login execution in github workflows (non-login shell)
# Add $PATH (Very important, or the following tools will be install once again due to it's not in non-login shell path)
export PATH="$HOME/.local/bin:$HOME/.local/share/pnpm:$PATH"

# install uv for python (only if not installed)
if ! command -v uv &>/dev/null; then
	echo "Installing uv..." # in $HOME/.local/bin
	wget -qO- https://astral.sh/uv/install.sh | sh
else
	echo "uv already installed. Skipping."
fi

# install pnpm (only if not installed)
if ! command -v pnpm &>/dev/null; then
	echo "Installing pnpm..." # in $HOME/.local/share/pnpm
	wget -qO- https://get.pnpm.io/install.sh | sh -
else
	echo "pnpm already installed. Skipping."
fi

# install git (only if not installed)
if ! command -v git &>/dev/null; then
	echo "Installing Git..." # in /usr/bin
	sudo apt install -y git
else
	echo "Git already installed. Skipping."
fi

#! ENV var defines
BACKEND_ROOT_DIR="$PROJECT_ROOT_LOCAL_DIR/backend"
GUNICORN_BIN="$BACKEND_ROOT_DIR/.venv/bin/gunicorn"
SYSTEMD_SERVICE_FILE_NAME="docgate-fastapi.service"

# Following ENV vars are machine specific
# 如果存在 .machine.env，则引入它
# 注意：即使文件里定义了变量，也会被后续逻辑判断是否保留
if [ -f "$SCRIPT_DIR/.machine.env" ]; then
	source "$SCRIPT_DIR/.machine.env"
fi

# 3. 使用 : "${VAR:=DEFAULT}" 语法: 如果变量未设置或为空，则赋值为等号后面的默认值
: "${ENV:="prod"}"
: "${CONF_SYNC_GIT_REPO_LOCAL_DIR:="/root/github/private-conf/web/docgate/confgen"}"
: "${NGINX_SYSTEM_CONF_DIR:="/etc/nginx/conf.d"}"
# following 3 are used for GunicornSyslogLogger
: "${SYSLOG_ADDRESS:="127.0.0.1:11514"}"
: "${SYSLOG_HOSTNAME:="docgate.fastapi"}"
: "${SYSLOG_TAG:="docgate_fastapi"}"
# * export `PATH` so the following scripts don't need to worry about the key binary usage
cat >$SCRIPT_DIR/.env <<EOF

ENV="$ENV"
PROJECT_ROOT_LOCAL_DIR="$PROJECT_ROOT_LOCAL_DIR"
CONF_SYNC_GIT_REPO_LOCAL_DIR="$CONF_SYNC_GIT_REPO_LOCAL_DIR"
NGINX_SYSTEM_CONF_DIR="$NGINX_SYSTEM_CONF_DIR"
SYSTEMD_SERVICE_FILE_NAME="${SYSTEMD_SERVICE_FILE_NAME}"
BACKEND_ROOT_DIR="$BACKEND_ROOT_DIR"
PATH="$PATH"

EOF

# write the systemd service file.
cat >"$SCRIPT_DIR/${SYSTEMD_SERVICE_FILE_NAME}" <<EOF
[Unit]
Description=Docgate FastAPI App
After=network.target

[Service]
Type=notify
NotifyAccess=all

# NOTE: here I just set it to root. Change as your actual condition.
User=root
Group=root
WorkingDirectory=$BACKEND_ROOT_DIR
Environment="ENV=$ENV"
# required by gunicorn & fastapi service logger
Environment="SYSLOG_ADDRESS=$SYSLOG_ADDRESS"
Environment="SYSLOG_HOSTNAME=$SYSLOG_HOSTNAME"
Environment="SYSLOG_TAG=$SYSLOG_TAG"

# Note: I set worker=1.
ExecStart=$GUNICORN_BIN \\
  -c file:${SCRIPT_DIR}/gunicorn.conf.py \\
	docgate.app:app \\

ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed

WatchdogSec=180
# not too short, but not too long - it may just hang, restart(kill&start) will fix it.
TimeoutStartSec=30
TimeoutStopSec=20
RestartSec=5
Restart=always

[Install]
WantedBy=multi-user.target

EOF
