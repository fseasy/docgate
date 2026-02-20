from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

EnvT = Literal["dev", "staging", "prod"]


# ! NOTE: We keep the key name as the .env name for simplify, so it's not a good example for Python code style


class BasicConfigT(BaseModel):
  VITE_APP_NAME: str  # any key with `VITE` prefix means it will be used in REACT vite framework
  VITE_APP_LOCALE_NAME: str  # in locale
  VITE_CONTENT_AUTHOR_NAME: str
  # * site-api
  VITE_API_DOMAIN: str
  VITE_API_COMMON_BASE_PATH: str
  VITE_API_AUTH_BASE_PATH: str
  # * site-frontend
  # use this common base path to make the Nginx route react/hugo part more easily.
  VITE_WEBSITE_DOMAIN: str
  VITE_WEBSITE_REACT_BASE_PATH: str
  VITE_WEBSITE_AUTH_BASE_PATH: str
  VITE_WEBSITE_DOC_ROOT_PATH: str
  VITE_WEBSITE_INDEX_ROOT_PATH: str
  # * frontend public route (used in other place beyond frontend)


class SupertokensConfT(BaseModel):
  SUPERTOKENS_CONNECTION_URI: str
  SUPERTOKENS_API_KEY: str


class StripeConfT(BaseModel):
  VITE_STRIPE_RETURN_ROUTE_PATH: str
  VITE_STRIPE_PUBLISHABLE_API_KEY: str
  STRIPE_API_KEY: str
  STRIPE_ENDPOINT_SECRET: str
  STRIPE_PRICE_ID: str


class SupabaseConfT(BaseModel):
  SUPABASE_USER: str
  SUPABASE_PASSWD: str
  SUPABASE_HOST: str
  SUPABASE_PORT: int
  SUPABASE_DBNAME: str


class SMTPConfT(BaseModel):
  SMTP_HOST: str
  SMTP_PORT: int
  SMTP_ACCOUNT_EMAIL: str
  SMTP_ACCOUNT_PASSWD: str
  SMTP_SECURE: bool


def _gen_abs_dir(rel_dir: str, check: bool = True) -> Path:
  _cur = Path(__file__).parent
  abs_dir = _cur / rel_dir
  abs_dir = abs_dir.resolve().absolute()
  if check:
    assert abs_dir.exists(), f"{rel_dir} (abs-path={abs_dir}) Not exists!"
  return abs_dir


class NginxConfT(BaseModel):
  standard_reverse_proxy: bool = False
  """If true, 
  - will ignore the `listen_port` and listen 80 & 443 on ipv4 & ipv6 public network.
    It will create 2 server blocks: a. 443 block (main) b. 80 block that is redirected to the 443
  - will assert server_name not None
  - will assert SSL config not None and not empty
  """
  listen_port: int = 3333
  server_name: str | None = None
  ssl_conf_lines: list[str] | None = None
  access_log_path: Path | None = Field(default=_gen_abs_dir("../nginx/log/access.log", check=False))


def _gen_default_hugo_public_doc_paths() -> set[str]:
  """Note: the path/link should not contain the /docs/ prefix
  i.e.:
  real-path    | sub-path
  /docs/       | ""
  /docs/page1  | page1
  /docs/page2/ | page2 (you don't need to add the trailing slash)
  """
  sub_paths = [
    "",  # doc root
    "010-update-log",
    "020-usage-manual",
    "030-routine-care",
    "030-routine-care/getup",
    "030-routine-care/020-putting-on-clothes",
  ]
  return set(sub_paths)


class DeployConfT(BaseModel):
  vite_in_server_mode: bool
  backend_server: str = "127.0.0.1:3001"  # fastapi default value
  vite_server: str = "127.0.0.1:5173"  # vite default value
  vite_static_dir: str | None
  hugo_static_dir: str
  hugo_public_doc_paths: set[str] | None = Field(default_factory=_gen_default_hugo_public_doc_paths)
  nginx: NginxConfT = NginxConfT()


class ModuleDirT(BaseModel):
  backend: Path = Field(description="backend dir", default=_gen_abs_dir("../docgate"))
  vite: Path = Field(description="vite dir", default=_gen_abs_dir("../frontend"))
  nginx: Path = Field(description="nginx conf dir", default=_gen_abs_dir("../nginx"))


class EnvConfT(BaseModel):
  basic: BasicConfigT
  supertokens: SupertokensConfT
  stripe: StripeConfT
  supabase: SupabaseConfT
  smtp: SMTPConfT
  deploy: DeployConfT
  module_dir: ModuleDirT = ModuleDirT()


class BackupManager(object):
  def __init__(self, env: EnvT):
    import time

    sig = time.strftime("%m%d-%H%M%S")
    self._cur_dir = _gen_abs_dir(f"./backup/{env}/{sig}", check=False)
    self._cur_dir.mkdir(parents=True, exist_ok=True)

  def backup(self, src_path: Path, name: str):
    import shutil

    if not src_path.exists():
      return
    tgt_path = self._cur_dir / name
    shutil.move(src_path, tgt_path)
