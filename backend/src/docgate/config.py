import logging
import os
import sys
from collections import namedtuple
from enum import StrEnum
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fs_pyutils.log_builder import SyslogLogField, build_logger

from docgate.utils import normalize_fastapi_base_path


class Env(StrEnum):
  DEV = "dev"
  STAGING = "staging"
  PROD = "prod"


class _EnvVarLoader:
  _ENV2SUFFIX: dict[Env, str] = {Env.DEV: "dev", Env.STAGING: "staging", Env.PROD: "prod"}
  _ENV_FILE_DIR = Path(__file__).parent.absolute()  # same as the module dir.

  @classmethod
  def load_from_dotenv(cls, env: Env) -> None:
    env_file_suffix = cls._ENV2SUFFIX[env]
    client_shared_conf_path = cls._ENV_FILE_DIR / f".env.client_shared.{env_file_suffix}"
    server_conf_path = cls._ENV_FILE_DIR / f".env.server.{env_file_suffix}"
    print(f"> docgate: load client shared conf from [{client_shared_conf_path}]", file=sys.stderr)
    load_dotenv(client_shared_conf_path)
    print(f"> docgate: load client shared conf from [{server_conf_path}]", file=sys.stderr)
    load_dotenv(server_conf_path)


_env_str = os.getenv("env") or os.getenv("ENV")


if not _env_str:
  raise RuntimeError("No `ENV` variable is exported before running! set `ENV=dev` or `ENV=prod`!")
try:
  env = Env(_env_str)
except ValueError as e:
  raise RuntimeError(f"Invalid ENV value: {_env_str}, candidates={[v for v in Env]}") from e

_EnvVarLoader.load_from_dotenv(env)

APP_NAME = os.environ["VITE_APP_NAME"]
APP_LOCALE_NAME = os.environ["VITE_APP_LOCALE_NAME"]
CONTENT_AUTHOR_NAME = os.environ["VITE_CONTENT_AUTHOR_NAME"]
_syslog_addr_str = os.environ["SYSLOG_RECEIVER_ADDR"]

if _value := _syslog_addr_str.strip():
  _host, _port = _value.split(":")
  _addr: tuple[str, int] | None = (_host, int(_port))
else:
  _addr = None

API_DOMAIN = os.environ["VITE_API_DOMAIN"]


_syslog_field = SyslogLogField(host=API_DOMAIN, tag="docgate_fastapi")
LOGGER = build_logger(
  APP_NAME, logging.DEBUG if env == Env.DEV else logging.INFO, syslog_address=_addr, syslog_log_field=_syslog_field
)

LOGGER.info(f"Loaded client and server environmental vars for ENV={env}")

# only normalize our self one
API_COMMON_BASE_PATH = normalize_fastapi_base_path(os.environ["VITE_API_COMMON_BASE_PATH"])
API_AUTH_BASE_PATH = os.environ["VITE_API_AUTH_BASE_PATH"]
WEBSITE_DOMAIN = os.environ["VITE_WEBSITE_DOMAIN"]
WEBSITE_REACT_BASE_PATH = os.environ["VITE_WEBSITE_REACT_BASE_PATH"]
WEBSITE_AUTH_BASE_PATH = os.environ["VITE_WEBSITE_AUTH_BASE_PATH"]
STRIPE_RETURN_ROUTE_PATH = os.environ["VITE_STRIPE_RETURN_ROUTE_PATH"]

SUPERTOKENS_CONNECTION_URI = os.environ["SUPERTOKENS_CONNECTION_URI"]
SUPERTOKENS_API_KEY = os.environ["SUPERTOKENS_API_KEY"]
STRIPE_API_KEY = os.environ["STRIPE_API_KEY"]
STRIP_PRICE_ID = os.environ["STRIPE_PRICE_ID"]
STRIP_ENDPOINT_SECRET = os.environ["STRIPE_ENDPOINT_SECRET"]

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
  q: dict[str, str] = {"show": show}
  if redirect:
    q["redirectToPath"] = redirect
  u = u.with_query(q)
  return str(u)


def get_website_full_url(sub_path: str, query_params: dict[str, str] | None = None) -> str:
  from yarl import URL

  no_leading_slash_sub_path = sub_path.lstrip("/")
  u = URL(WEBSITE_DOMAIN) / no_leading_slash_sub_path
  if query_params:
    u = u.with_query(query_params)
  return str(u)


# Some Global config
EMAIL_VERIFICATION_REQUIRED = True  # require email verification
