
# mainly for log
ENV=dev uv run alembic revision --autogenerate
ENV=dev uv run alembic upgrade head
