from datetime import datetime, timezone
from enum import IntEnum
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ValidationError
from sqlalchemy import Boolean, DateTime, Dialect, ForeignKey, Integer, NullPool, String, Text, TypeDecorator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .config import LOGGER as logger, env
from .exceptions import LogicError
from .utils import safe_strftime


# Define enums
class PayMethod(IntEnum):
  PREPAID_CODE = 0
  PAYWALL = 1

  def locale_name(self) -> str:
    m = {PayMethod.PREPAID_CODE: "预付款码", PayMethod.PAYWALL: "页面自购"}
    return m[self]


class Tier(IntEnum):
  INTERNAL_MANAGER = 0
  INTERNAL = 1
  FREE = 2
  GOLD = 3

  def locale_name(self) -> str:
    tier_map = {Tier.FREE: "免费", Tier.GOLD: "付费", Tier.INTERNAL: "内部用户", Tier.INTERNAL_MANAGER: "管理员"}
    return tier_map[self]


# def _get_sqlite_db_async_path() -> str:
#   from pathlib import Path

#   _workspace_dir = Path(__file__).parent
#   p = f"sqlite+aiosqlite:///{_workspace_dir / 'sqlite.db'}"
#   return p


def _get_postgresql_async_uri() -> str:
  from .config import SUPABASE_CONF as c

  s = f"postgresql+asyncpg://{c.user}:{c.passwd}@{c.host}:{c.port}/{c.dbname}"
  return s


# you can set `echo=True` for debug
async_engine = create_async_engine(_get_postgresql_async_uri(), poolclass=NullPool)
"""Async engine"""

AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
"""Async Session maker instance"""


class IntEnumDecorator(TypeDecorator):
  """Save IntEnum as Int in DB, but read as IntEnum as Python."""

  impl = Integer  # tell the the impl

  def __init__(self, enum_class: type[IntEnum], *args: Any, **kwargs: Any):
    super().__init__(*args, **kwargs)
    self.enum_class = enum_class

  def process_bind_param(self, value: None | IntEnum, dialect: Dialect) -> int | None:
    """write"""
    del dialect
    if value is None:
      return None
    if isinstance(value, self.enum_class):
      return value.value
    return value

  def process_result_value(self, value: int | None, dialect: Dialect) -> IntEnum | None:
    """read"""
    del dialect
    if value is None:
      return None
    return self.enum_class(value)


class TZDateTime(TypeDecorator):
  """Save & Load always keep the UTC tz.
  - in DB: no tz info
  - in application: always has tz

  WHY: make no-tz info has better compatibility across different db (sqlite didn't reserve tz info)

  write-flow: 1. assert input has tz. 2. transform to utc tz 3. remove tz and put to db
  read-flow: 1. read from db, add utc tz
  """

  # ! impl type, This is Datetime without TZ.
  # Tips: DateTime(timezone=True) let the db create datetime with tz. But sqlite don't support it.
  impl = DateTime
  cache_ok = True  # allow SQLAlchemy cache

  def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
    """write flow: transform to UTC, then remove tz info"""
    if value is None:
      return None
    if not value.tzinfo:
      raise LogicError(f"DB input time must have tz info while [{value}] doesn't have")

    utc_value = value.astimezone(ZoneInfo("UTC"))
    clean_value = utc_value.replace(tzinfo=None)
    return clean_value  # noqa: RET504

  def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
    """read flow: add UTC tz info"""
    if value is None:
      return None
    return value.replace(tzinfo=ZoneInfo("UTC"))  # noqa: UP017


class DbBaseModel(DeclarativeBase):
  pass


class PayLogUnit(BaseModel):
  """Please use `PayLog.create_new_unit` to create new instance as it will accept the enum"""

  method: str | None  # directly store the name to save space.
  log: str
  is_success: bool
  date: str


class PayLog(BaseModel):
  logs: list[PayLogUnit]

  def add_new(self, log: str, method: PayMethod | None, is_success: bool) -> PayLogUnit:
    new_unit = self.create_new_unit(log, method=method, is_success=is_success)
    self.logs.append(new_unit)
    return new_unit

  def to_db_str(self) -> str:
    return self.model_dump_json(indent=None, ensure_ascii=False)

  @classmethod
  def create_new_unit(cls, log: str, method: PayMethod | None, is_success: bool) -> PayLogUnit:
    method_name = method.locale_name() if method is not None else None
    new_unit = PayLogUnit(
      log=log, method=method_name, is_success=is_success, date=datetime.now(tz=timezone.utc).isoformat()
    )
    return new_unit

  @classmethod
  def from_db_str(cls, log_str: str | None) -> "PayLog":
    if not log_str:
      return cls(logs=[])
    try:
      d = cls.model_validate_json(log_str)
    except ValidationError as e:
      logger.warning(f"Unexpected paylog format, err={e}. Let's transform it to new format")
      d = cls(logs=[])
      d.add_new(
        f"TRANS Legacy FORMAT with reset success flag: {log_str}", method=None, is_success=False
      )  # set the default success to True
    return d

  @classmethod
  def db_add_new2current(
    cls, current_log_serialized_str: str | None, new_log_str: str, method: PayMethod | None, is_success: bool
  ) -> str:
    """A helper function for db: Deserialize the current log and append new, then serialize to str"""
    cur_log = cls.from_db_str(current_log_serialized_str)
    cur_log.add_new(new_log_str, method=method, is_success=is_success)
    return cur_log.to_db_str()


USER_TABLE_NAME_WITH_ENV = f"users_{env.value}"  # add a env suffix due to no env independent db


class User(DbBaseModel):
  __tablename__ = USER_TABLE_NAME_WITH_ENV

  id: Mapped[str] = mapped_column(String(36), primary_key=True)  # for external user id
  email: Mapped[str] = mapped_column(String(100), index=True)
  # datetime In UTC tz while don't contain tz info
  created_at: Mapped[datetime] = mapped_column(TZDateTime, default=lambda: datetime.now(tz=timezone.utc))
  # only record when db side changes.
  last_active_at: Mapped[datetime] = mapped_column(
    TZDateTime,
    default=lambda: datetime.now(tz=timezone.utc),
    onupdate=lambda: datetime.now(tz=timezone.utc),
  )
  tier: Mapped[Tier] = mapped_column(IntEnumDecorator(Tier))
  """Used to decide user payment, with tier_lifetime constraints"""
  tier_lifetime: Mapped[datetime | None] = mapped_column(TZDateTime, nullable=True)

  """A json object. see the PayLog object
  pay_log are auxiliary fields and should not be used to determine payment status
  """
  pay_log: Mapped[str] = mapped_column(Text, default="")  # log for payment (success, error, history)
  # currently it's always None because it's always lifelong

  # one user may have 0/multiple prepaid-codes (in the future>>>). only relationship in ORM level
  prepaid_codes: Mapped[list["PrepaidCode"]] = relationship(
    back_populates="bind_user",
    passive_deletes=True,  # Let the db `SET NULL`
  )

  def __str__(self) -> str:
    # no relationship print
    return (
      f"User(id=[{self.id}], email=[{self.email}], created_at=[{safe_strftime(self.created_at)}]"
      f", last_active_at=[{safe_strftime(self.last_active_at)}]"
      f", tier=[{self.tier.name})], lifetime=[{safe_strftime(self.tier_lifetime)}]"
      f", pay_log=[{self.pay_log}]"
    )

  def add_paylog(self, log_str: str, method: PayMethod | None, is_success: bool) -> str:
    new_log = PayLog.db_add_new2current(self.pay_log, log_str, method=method, is_success=is_success)
    self.pay_log = new_log
    return new_log

  @property
  def continuous_pay_failure_cnt(self):
    """count continuous failure count"""
    log = PayLog.from_db_str(self.pay_log)
    cnt = 0
    for unit in reversed(log.logs):
      if not unit.is_success:
        cnt += 1
      else:
        break
    return cnt


INVITE_TABLE_NAME_WITH_ENV = f"prepaid_codes_{env.value}"


class PrepaidCode(DbBaseModel):
  __tablename__ = INVITE_TABLE_NAME_WITH_ENV

  CODE_LEN = 10

  id: Mapped[int] = mapped_column(primary_key=True)
  code: Mapped[str] = mapped_column(String(CODE_LEN), index=True)
  lifetime: Mapped[datetime] = mapped_column(TZDateTime)
  has_used: Mapped[bool] = mapped_column(Boolean(), default=False)
  bind_user_id: Mapped[str | None] = mapped_column(
    ForeignKey(f"{USER_TABLE_NAME_WITH_ENV}.id", ondelete="SET NULL"),  # Set to Null when user-id get deleted
    nullable=True,
    default=None,
    index=True,
  )

  bind_user: Mapped[User | None] = relationship(back_populates="prepaid_codes")

  def do_binding(self, user_id: str) -> None:
    self.has_used = True
    self.bind_user_id = user_id

  @property
  def redeemable_with_reason(self) -> tuple[bool, str | None]:
    if self.has_used:
      return (False, f"<{self}> has already been used.")
    lifetime = self.lifetime
    if datetime.now(timezone.utc) > lifetime:
      return (False, f"<{self}> has expired.")
    return (True, None)

  def __str__(self) -> str:
    # no relationship print
    return (
      f"PrepaidCode(id=[{self.id}], code=[{self.code}], lifetime=[{safe_strftime(self.lifetime)}], "
      f"has_used=[{self.has_used}], bind_user_id=[{self.bind_user_id}])"
    )


async def create_all_tables():
  async with async_engine.begin() as conn:
    await conn.run_sync(DbBaseModel.metadata.create_all)


async def drop_all_tables():
  async with async_engine.begin() as conn:
    await conn.run_sync(DbBaseModel.metadata.drop_all)


async def dispose_engine():
  """Call this when you need to exit the APP! or the app will hang forever!"""
  await async_engine.dispose()
