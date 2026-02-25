#!/usr/bin/env bash
# run dev backend + frontend

cd frontend && pnpm run dev &
cd ..
cd docgate && ./run_dev.sh