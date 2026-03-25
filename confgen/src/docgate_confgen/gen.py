import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .data_types import BackupManager, EnvConfT, EnvT
from .nginx_conf_gen import NginxConfGen

g_backup: BackupManager | None = None


def main(env: EnvT) -> None:
  global g_backup

  g_backup = BackupManager(env)

  conf = _get_env_conf(env)
  _gen_backend_conf(env, conf)
  _gen_vite_conf(env, conf)
  _gen_nginx_conf(env, conf)


def _get_env_conf(env: EnvT) -> EnvConfT:
  if env == "dev":
    from .unified_conf.dev.conf import Conf as dev_conf

    return dev_conf
  if env == "prod":
    from .unified_conf.prod.conf import Conf as prod_conf

    return prod_conf
  if env == "staging":
    from .unified_conf.staging.conf import Conf as staging_conf  # type: ignore

    return staging_conf

  raise ValueError(f"failed to load unified-env as invalid env value: {env}")


def _gen_backend_conf(env: EnvT, c: EnvConfT) -> None:
  backend_dir = c.module_dir.backend
  # make independent env to make debug easier
  env2suffix: dict[EnvT, str] = {"dev": "dev", "staging": "staging", "prod": "prod"}
  suffix = env2suffix[env]
  # back-compatibility for manual management
  shared_conf_path = backend_dir / f".env.client_shared.{suffix}"

  assert g_backup
  g_backup.backup(shared_conf_path, "shared.env")
  _write_dict2env_file(_get_vite_backend_shared_data(c), shared_conf_path)

  server_conf_path = backend_dir / f".env.server.{suffix}"
  syslog_addr = c.deploy.syslog_receiver_address
  if syslog_addr:
    _syslog_receiver_addr_env_value = f"{syslog_addr.host}:{syslog_addr.port}"
  else:
    _syslog_receiver_addr_env_value = ""
  server_data = {
    **_model2dict(c.supertokens, None),
    **_model2dict(c.supabase, None),
    **_model2dict(c.smtp, None),
    **_model2dict(c.stripe, ["STRIPE_API_KEY", "STRIPE_ENDPOINT_SECRET", "STRIPE_PRICE_ID"]),
    # extra
    "SYSLOG_RECEIVER_ADDR": _syslog_receiver_addr_env_value,
  }
  g_backup.backup(server_conf_path, "backend_server.env")
  _write_dict2env_file(server_data, server_conf_path)
  print(f"WRITE> backend-conf: shared={shared_conf_path}, server={server_conf_path}", file=sys.stderr)


def _gen_vite_conf(env: EnvT, c: EnvConfT) -> None:
  vite_dir = c.module_dir.vite
  #! note: here we also mapping staging to production name, so we can just use the default `build` param
  env2vite_default_suffix: dict[EnvT, str] = {
    "dev": "development.local",
    "staging": "production.local",
    "prod": "production.local",
  }
  suffix = env2vite_default_suffix[env]
  env_path = vite_dir / f".env.{suffix}"
  _write_dict2env_file(_get_vite_backend_shared_data(c), env_path)
  print(f"WRITE> vite-env-conf: {env_path}", file=sys.stderr)


def _gen_nginx_conf(env: EnvT, c: EnvConfT) -> None:
  gen = NginxConfGen(c)
  out_path = c.module_dir.nginx / f"{env}.conf"
  assert g_backup
  g_backup.backup(out_path, "nginx.conf")

  gen.gen(out_path)
  print(f"WRITE> nginx-conf: {out_path}", file=sys.stderr)
  print("NOTE> please `ln -s` this file to nginx server conf dir", file=sys.stderr)
  print("      In mac+brew, it should be: ", file=sys.stderr)
  print(f"      - `cd /opt/homebrew/etc/nginx/servers && ln -s {out_path} docgate-{env}.conf`", file=sys.stderr)
  print(
    "   You just need to link once, the symbolic link will keep the content updated once you update it here",
    file=sys.stderr,
  )


def _get_vite_backend_shared_data(c: EnvConfT) -> dict[str, Any]:
  return {
    **_model2dict(c.basic, None),
    **_model2dict(c.stripe, ["VITE_STRIPE_RETURN_ROUTE_PATH", "VITE_STRIPE_PUBLISHABLE_API_KEY"]),
  }


def _model2dict(m: BaseModel, keys: list[str] | None) -> dict[str, Any]:
  if keys is None:
    return m.model_dump(mode="python")
  return {k: getattr(m, k) for k in keys}


def _write_dict2env_file(env_dict: dict[str, Any], file_path: Path) -> None:
  import shlex

  with open(file_path, "w", encoding="utf-8") as f:
    for key, value in env_dict.items():
      safe_value = shlex.quote(str(value))
      f.write(f"{key}={safe_value}\n")
