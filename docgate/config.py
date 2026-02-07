import logging
import os
from collections import namedtuple
from enum import StrEnum
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

from docgate.log_builder import build_logger
from docgate.utils import normalize_fastapi_base_path


class Env(StrEnum):
  DEV = "dev"
  PROD = "prod"


_env_str = os.getenv("env") or os.getenv("ENV")


if not _env_str:
  raise RuntimeError("No `ENV` variable is exported before running! set `ENV=dev` or `ENV=prod`!")
try:
  env = Env(_env_str)
except ValueError:
  raise RuntimeError(f"Invalid ENV value: {_env_str}, candidates={[v for v in Env]}")

_root_dir = Path(__file__).parent.absolute()
_client_shared_prod_conf_path = _root_dir / ".env.client_shared.production"
_client_shared_dev_conf_path = _root_dir / ".env.client_shared.local"
_server_dev_conf_path = _root_dir / ".env.server.local"
_server_prod_conf_path = _root_dir / ".env.server.production"

if env == Env.PROD:
  load_dotenv(_client_shared_prod_conf_path)
  load_dotenv(_server_prod_conf_path)
else:
  load_dotenv(_client_shared_dev_conf_path)
  load_dotenv(_server_dev_conf_path)


APP_NAME = os.environ["VITE_APP_NAME"]
APP_LOCALE_NAME = os.environ["VITE_APP_LOCALE_NAME"]

LOGGER = build_logger(APP_NAME, logging.DEBUG if env == Env.DEV else logging.INFO)

LOGGER.info(f"Loaded client and server environmental vars for ENV={env}")

API_DOMAIN = os.environ["VITE_API_DOMAIN"]
# only normalize our self one
API_COMMON_BASE_PATH = normalize_fastapi_base_path(os.environ["VITE_API_COMMON_BASE_PATH"])
API_AUTH_BASE_PATH = os.environ["VITE_API_AUTH_BASE_PATH"]
WEBSITE_DOMAIN = os.environ["VITE_WEBSITE_DOMAIN"]
WEBSITE_AUTH_BASE_PATH = os.environ["VITE_WEBSITE_AUTH_BASE_PATH"]
SUPERTOKENS_CONNECTION_URI = os.environ["SUPERTOKENS_CONNECTION_URI"]
SUPERTOKENS_API_KEY = os.environ["SUPERTOKENS_API_KEY"]

_SupabaseConfT = namedtuple("_SupabaseConfT", ["host", "port", "user", "passwd", "dbname"])
SUPABASE_CONF = _SupabaseConfT(
  host=os.environ["SUPABASE_HOST"],
  port=int(os.environ["SUPABASE_PORT"]),
  user=os.environ["SUPABASE_USER"],
  passwd=os.environ["SUPABASE_PASSWD"],
  dbname=os.environ["SUPABASE_DBNAME"],
)

_SMTPConf = namedtuple("_SMTPConf", ["host", "port", "account_email", "account_name", "account_password", "secure"])
SMTP_CONF = _SMTPConf(
  host=os.environ["SMTP_HOST"],
  port=os.environ["SMTP_PORT"],
  account_email=os.environ["SMTP_ACCOUNT_EMAIL"],
  account_name=APP_LOCALE_NAME,
  account_password=os.environ["SMTP_ACCOUNT_PASSWD"],
  secure=os.environ["SMTP_SECURE"].lower() == "true",
)


def get_st_auth_page_full_url(show: Literal["signin", "signup"], redirect: str | None) -> str:
  from yarl import URL

  no_leading_slash_auth_base = WEBSITE_AUTH_BASE_PATH.lstrip("/")
  u = URL(WEBSITE_DOMAIN) / no_leading_slash_auth_base
  q = {"show": show}
  if redirect:
    q["redirectToPath"] = redirect
  u = u.with_query(q)
  return str(u)
