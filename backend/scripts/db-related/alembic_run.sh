
# mainly for log
# RUN THIS in the project ROOT DIR (The dir that contains `alembic.ini` file)
ENV=dev uv run alembic revision --autogenerate
ENV=dev uv run alembic upgrade head
