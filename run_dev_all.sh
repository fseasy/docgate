#!/usr/bin/env bash
# run dev backend + frontend
set -euo pipefail

cleanup() {
  trap - EXIT INT TERM
  echo "Stopping all child processes..."
  pkill -P $$
}

trap cleanup EXIT INT TERM

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd $ROOT_DIR/frontend
pnpm run dev &

cd $ROOT_DIR/docgate
./run_dev.sh
