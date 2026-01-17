import logging
import os
import sys
from enum import StrEnum
from pathlib import Path

from dotenv import load_dotenv


class Env(StrEnum):
  DEV = "dev"
  PROD = "prod"


def _build_logger(name: str, level: int):
  logger = logging.getLogger(name)

  streamHander = logging.StreamHandler(stream=sys.stderr)
  fmt = logging.Formatter("%(asctime)s/%(name)s/%(levelname)s/%(filename)s:%(lineno)d> %(message)s")
  streamHander.setFormatter(fmt)
  streamHander.setLevel(level)
  logger.addHandler(streamHander)
  logger.setLevel(level)

  return logger


_env_str = os.getenv("env") or os.getenv("ENV")


if not _env_str:
  raise RuntimeError("No `ENV` variable is exported before running! set `ENV=dev` or `ENV=prod`!")
try:
  env = Env(_env_str)
except ValueError:
  raise RuntimeError(f"Invalid ENV value: {_env_str}, candidates={[v for v in Env]}")

_root_dir = Path(__file__).parent.absolute()
_shared_dev_conf_path = _root_dir / ".env.local"
_shared_prod_conf_path = _root_dir / ".env.production"

if env == Env.PROD:
  _shared_conf_path = _shared_prod_conf_path
else:
  _shared_conf_path = _shared_dev_conf_path
load_dotenv(_shared_conf_path)

APP_NAME = os.environ["VITE_APP_NAME"]

LOGGER = _build_logger(APP_NAME, logging.DEBUG if env == Env.DEV else logging.INFO)

LOGGER.info(f"Loaded shared env from [{_shared_conf_path}]")

API_DOMAIN = os.environ["VITE_API_DOMAIN"]
WEBSITE_DOMAIN = os.environ["VITE_WEBSITE_DOMAIN"]
