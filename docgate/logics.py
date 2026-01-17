import uuid
from datetime import datetime, timedelta


class InviteCode(object):
  @staticmethod
  def code_len():
    INVITE_CODE_LEN = 10
    return INVITE_CODE_LEN

  @staticmethod
  def gen_invite_code():
    """Just use uuid to generate an invite code"""
    code = str(uuid.uuid4()).replace("-", "")[: InviteCode.code_len()]
    return code

  @staticmethod
  def get_lifetime(base: datetime | None = None) -> datetime:
    EXPIRE_DAYS = 14

    if not base:
      base = datetime.now()
    return base + timedelta(days=EXPIRE_DAYS)
