import argparse
from pathlib import Path
from typing import Any
from pydantic import BaseModel
from confgen.data_types import EnvConfT, EnvT, BackupManager


g_backup = None


def main():
  global g_backup

  parser = argparse.ArgumentParser(description="Config generator")
  parser.add_argument("--env", "-e", required=True, choices=EnvT.__args__, help="generate which env")
  args = parser.parse_args()

  g_backup = BackupManager()

  env = args.env
  conf = _get_env_conf(env)
  _gen_backend_conf(env, conf)
  _gen_vite_conf(env, conf)


def _get_env_conf(env: EnvT) -> EnvConfT:
  import importlib

  module_name = f"confgen.uni-conf.{env}.conf"
  c = importlib.import_module(module_name)
  conf: EnvConfT = c.Conf
  return conf


def _gen_backend_conf(env: EnvT, c: EnvConfT):
  backend_dir = c.module_dir.backend
  env2suffix: dict[EnvT, str] = {"dev": "local", "staging": "staging", "prod": "production"}
  suffix = env2suffix[env]
  # back-compatibility for manual management
  shared_conf_path = backend_dir / f".env.client_shared.{suffix}"

  g_backup.backup(shared_conf_path, "shared.env")
  _write_dict2env_file(_get_vite_backend_shared_data(c), shared_conf_path)

  server_conf_path = backend_dir / f".env.server.{suffix}"
  server_data = {
    **_model2dict(c.supertokens, None),
    **_model2dict(c.supabase, None),
    **_model2dict(c.smtp, None),
    **_model2dict(c.stripe, ["STRIPE_API_KEY", "STRIPE_ENDPOINT_SECRET", "STRIPE_PRICE_ID"]),
  }
  g_backup.backup(server_conf_path, "backend_server.env")
  _write_dict2env_file(server_data, server_conf_path)


def _gen_vite_conf(env: EnvT, c: EnvConfT):
  vite_dir = c.module_dir.vite
  env2suffix: dict[EnvT, str] = {"dev": "local", "staging": "staging", "prod": "production"}
  suffix = env2suffix[env]
  env_path = vite_dir / f".env.{suffix}"
  _write_dict2env_file(_get_vite_backend_shared_data(c), env_path)


def _get_vite_backend_shared_data(c) -> dict[str, Any]:
  shared_data = {
    **_model2dict(c.basic, None),
    **_model2dict(c.stripe, ["VITE_STRIPE_RETURN_ROUTE_PATH", "VITE_STRIPE_PUBLISHABLE_API_KEY"]),
  }
  return shared_data


def _model2dict(m: BaseModel, keys: list[str] | None) -> dict[str, Any]:
  if keys is None:
    return m.model_dump(mode="python")
  return {k: getattr(m, k) for k in keys}


def _write_dict2env_file(env_dict: dict[str, Any], file_path: Path):
  import shlex

  with open(file_path, "w", encoding="utf-8") as f:
    for key, value in env_dict.items():
      safe_value = shlex.quote(str(value))
      f.write(f"{key}={safe_value}\n")


if __name__ == "__main__":
  main()
