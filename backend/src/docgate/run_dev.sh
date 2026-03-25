#/usr/bin/env bash
set -euo pipefail

cleanup() {
  trap - EXIT INT TERM
  echo "Stopping all child processes..."
  pkill -P $$
}

trap cleanup EXIT INT TERM


echo "run the syslog receiver"

uv run python ./scripts/dummy_syslog_receiver.py &

echo "run docgate api"
ENV=dev uv run fastapi dev app.py --port 3001
