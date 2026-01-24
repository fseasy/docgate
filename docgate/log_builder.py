import logging
import sys
# import traceback


def build_logger(name: str, level: int):
  logger = logging.getLogger(name)

  streamHandler = logging.StreamHandler(stream=sys.stderr)
  fmt = SingleLineFormatter("%(asctime)s/%(name)s/%(levelname)s/%(filename)s:%(lineno)d> %(message)s")
  streamHandler.setFormatter(fmt)
  streamHandler.setLevel(level)
  logger.addHandler(streamHandler)
  logger.setLevel(level)

  return logger


class SingleLineFormatter(logging.Formatter):
  def format(self, record):
    fmt_line = super().format(record)
    single_line = fmt_line.replace("\n", " ↵ ")
    return single_line
