from datetime import datetime
from enum import IntEnum, StrEnum

from peewee import AutoField, BooleanField, CharField, DateTimeField, IntegerField, Model, SqliteDatabase

from .logics import InviteCode as InviteCodeLogic


# Define enums
class PayMethod(StrEnum):
  INVITE_CODE = "invite_code"
  SELF_HOSTED_PAYWALL = "self_hosted_paywall"


class Tier(IntEnum):
  INTERNAL_MANAGER = 0
  INTERNAL = 1
  FREE = 2
  GOLD = 3


def _create_sqlite_db():
  from pathlib import Path

  _workspace_dir = Path(__file__).parent
  DB_PATH = f"{_workspace_dir / 'sqlite.db'}"
  return SqliteDatabase(DB_PATH)


db = _create_sqlite_db()


class DbBaseModel(Model):
  class Meta:
    database = db


class User(DbBaseModel):
  external_id = CharField(36, unique=True, index=True)  # for external user id
  email = CharField(100, index=True)
  create_at = DateTimeField(default=datetime.now)
  last_active_at = DateTimeField(default=datetime.now)
  pay_method = CharField(30, null=True)
  lifetime = DateTimeField(null=True)  # currently it's always None because it's always lifelong
  tier = IntegerField()


class InviteCode(DbBaseModel):
  id = AutoField()
  code = CharField(InviteCodeLogic.code_len(), index=True)
  lifetime = DateTimeField()
  has_used = BooleanField()

  def is_redeemable(self) -> tuple[bool, str | None]:
    if self.has_used:
      return (False, f"code={self} has already been used")
    if datetime.now() > self.lifetime:
      return (False, f"code={self} has expired(lifetime={self.lifetime})")
    return (True, None)
