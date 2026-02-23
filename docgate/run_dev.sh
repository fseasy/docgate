#/bin/sh

echo "run the syslog receiver"
uv run python ./scripts/dummy_syslog_receiver.py &
echo "run docgate api"
ENV=dev uv run fastapi dev app.py --port 3001