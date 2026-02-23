import json
import logging
import sys
from datetime import datetime
from logging.handlers import SysLogHandler

# import traceback
from typing import Any
from urllib.parse import urlparse


def build_logger(name: str, level: int, syslog_address: tuple[str, int] | None = None, domain: str | None = None):
  """
  Args:
    syslog_address: used for syslog (you can setup a grafana alloy), will send a json log
    domain: used in the json logger
  """
  logger = logging.getLogger(name)

  streamHandler = logging.StreamHandler(stream=sys.stderr)
  fmt = SingleLineFormatter("%(asctime)s/%(name)s/%(levelname)s/%(filename)s:%(lineno)d> %(message)s")
  streamHandler.setFormatter(fmt)
  streamHandler.setLevel(level)

  logger.addHandler(streamHandler)
  logger.setLevel(level)

  # syslog
  if syslog_address:
    try:
      syslog_handler = SysLogHandler(address=syslog_address)
      syslog_handler.ident = f"{name}-api: "  # 必须以冒号空格结尾，触发 Alloy 的 tag 识别

      json_fmt = JsonSyslogFormatter(domain)
      syslog_handler.setFormatter(json_fmt)
      syslog_handler.setLevel(level)
      logger.addHandler(syslog_handler)
    except Exception as e:
      logger.warning(f"Failed to add syslog, err={e}")
  return logger


class SingleLineFormatter(logging.Formatter):
  def format(self, record):
    fmt_line = super().format(record)
    single_line = fmt_line.replace("\n", " ↵ ")
    # naively append extra fields
    extra_kv = _get_extra_kv(record)
    if extra_kv:
      extra_line = json.dumps(extra_kv, ensure_ascii=False, default=str)
      single_line = f"{single_line} extra={extra_line}"
    return single_line


class JsonSyslogFormatter(logging.Formatter):
  def __init__(self, domain: str | None = None):
    super().__init__()
    if domain:
      self._host: str | None = urlparse(domain if "://" in domain else "https://" + domain).hostname
    else:
      self._host = None

  def format(self, record: logging.LogRecord):

    iso_time = datetime.fromtimestamp(record.created).astimezone().isoformat(timespec="seconds")

    log_data = {
      "time": iso_time,  # to align the loki receiver
      "level": record.levelname,
      "logger": record.name,
      "file": f"{record.filename}:{record.lineno}",
      "msg": record.getMessage(),
    }
    if self._host:
      log_data["host"] = self._host  # to align loki

    if record.exc_info:
      log_data["traceback"] = self.formatException(record.exc_info)

    # add info from extra={...}
    log_data.update(_get_extra_kv(record))

    # 4. 安全地转换为 JSON
    # default=str 非常关键！如果你传了 datetime 或者 UUID 对象，它能防止 json.dumps 崩溃
    return json.dumps(log_data, default=str)


def _get_extra_kv(record: logging.LogRecord) -> dict[str, Any]:
  RESERVED_ATTRS = set(
    (
      "args",
      "asctime",
      "created",
      "exc_info",
      "exc_text",
      "filename",
      "funcName",
      "levelname",
      "levelno",
      "lineno",
      "message",
      "module",
      "msecs",
      "msg",
      "name",
      "pathname",
      "process",
      "processName",
      "relativeCreated",
      "stack_info",
      "thread",
      "threadName",
      "taskName",
    )
  )
  extra_data: dict[str, Any] = {}
  for key, value in record.__dict__.items():
    if key not in RESERVED_ATTRS:
      extra_data[key] = value
  return extra_data
