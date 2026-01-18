from typing import Any


def safe_getattr(o: object | None, name: str, default: Any | None = None) -> Any:
  if o is None:
    return None
  return getattr(o, name, default)
