from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo


def safe_getattr(o: object | None, name: str, default: Any | None = None) -> Any:
  if o is None:
    return default
  return getattr(o, name, default)


def safe_strftime(t: datetime | None) -> str:
  if t is None:
    return "null"
  target_zone = ZoneInfo("Asia/Shanghai")
  return t.astimezone(target_zone).strftime("%Y/%m%d %H:%M %z")


def add_utc_tz_if_eligible(dt: datetime | None) -> datetime | None:
  if dt is None:
    return None
  if dt.tzinfo is None:
    return dt.replace(tzinfo=timezone.utc)
  return dt


def normalize_fastapi_base_path(p: str) -> str:
  """make a normalization on the env var"""
  if p.endswith("/"):
    p = p.rstrip("/")
  if not p.startswith("/"):
    p = f"/{p}"
  return p
