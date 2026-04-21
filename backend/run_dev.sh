#!/usr/bin/env bash
set -euo pipefail

cleanup() {
	trap - EXIT INT TERM
	echo "Stopping all child processes..."
	pkill -P $$
}

uv run python ./scripts/dummy_syslog_receiver.py &

uv sync --frozen --no-dev
ENV=dev uv run fastapi dev src/docgate/app.py --port 3001
