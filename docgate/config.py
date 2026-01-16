import os
import sys
from pathlib import Path
from enum import StrEnum
import logging

from dotenv import load_dotenv

class Env(StrEnum):
  DEV = "dev"
  PROD = "prod"


def _conf_logging(env: Env):
  if env == Env.DEV:
    loglevel = logging.DEBUG
  else:
    loglevel = logging.WARNING

  logging.basicConfig(
    level=loglevel,
    format="%(asctime)s/%(name)s/%(levelname)s/%(filename)s:%(lineno)d> %(message)s",
    handlers=[
      logging.StreamHandler(sys.stderr),
    ],
  )
  # 获取应用日志记录器
  logger = logging.getLogger("uvicorn")
  logger.setLevel(logging.INFO)  # 设置 uvicorn 的日志等级
  return logger


_env_str = os.getenv("env") or os.getenv("ENV")


if not _env_str:
  raise RuntimeError("No `ENV` variable is exported before running! set `ENV=dev` or `ENV=prod`!")
try:
  env = Env(_env_str)
except ValueError:
  raise RuntimeError(f"Invalid ENV value: {_env_str}, candidates={[v for v in Env]}")

_conf_logging(env)


_root_dir = Path(__file__).parent.absolute()
_shared_dev_conf_path = _root_dir / ".env.local"
_shared_prod_conf_path = _root_dir / ".env.production"

if env == Env.PROD:
  _shared_conf_path = _shared_prod_conf_path
else:
  _shared_conf_path = _shared_dev_conf_path
load_dotenv(_shared_conf_path)

APP_NAME = os.environ["VITE_APP_NAME"]

LOGGER = logging.getLogger(APP_NAME)

LOGGER.info(f"Loaded shared env from [{_shared_conf_path}]")

API_DOMAIN = os.environ["VITE_API_DOMAIN"]
WEBSITE_DOMAIN = os.environ["VITE_WEBSITE_DOMAIN"]
