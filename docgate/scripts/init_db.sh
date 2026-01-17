#!/bin/sh

# make sure you install the docgate
# - cd $WORKSPACE_ROOT
# - uv pip install -e .

uv run python -c "from docgate.models import Base, engine; Base.metadata.create_all(engine)"