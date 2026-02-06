from datetime import datetime, timezone
from enum import IntEnum
from zoneinfo import ZoneInfo

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, NullPool, String, Text, TypeDecorator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .config import env
from .exceptions import LogicError
from .utils import safe_getattr, safe_strftime


# Define enums
class PayMethod(IntEnum):
  INVITE_CODE = 0
  SELF_HOSTED_PAYWALL = 1


class Tier(IntEnum):
  INTERNAL_MANAGER = 0
  INTERNAL = 1
  FREE = 2
  GOLD = 3


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

  def __init__(self, enum_class, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.enum_class = enum_class

  def process_bind_param(self, value, dialect):
    """write"""
    del dialect
    if value is None:
      return None
    if isinstance(value, self.enum_class):
      return value.value
    return value

  def process_result_value(self, value, dialect):
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

  def process_bind_param(self, value, dialect):
    """write flow: transform to UTC, then remove tz info"""
    if value is None:
      return None
    if not value.tzinfo:
      raise LogicError(f"DB input time must have tz info while [{value}] doesn't have")

    utc_value = value.astimezone(ZoneInfo("UTC"))
    clean_value = utc_value.replace(tzinfo=None)
    return clean_value

  def process_result_value(self, value, dialect):
    """read flow: add UTC tz info"""
    if value is None:
      return None
    return value.replace(tzinfo=timezone.utc)


class DbBaseModel(DeclarativeBase):
  pass


USER_TABLE_NAME_WITH_ENV = f"users_{env.value}"
INVITE_TABLE_NAME_WITH_ENV = f"invite_codes_{env.value}"


class User(DbBaseModel):
  __tablename__ = USER_TABLE_NAME_WITH_ENV

  id: Mapped[str] = mapped_column(String(36), primary_key=True)  # for external user id
  email: Mapped[str] = mapped_column(String(100), index=True)
  # datetime In UTC tz while don't contain tz info
  created_at: Mapped[datetime] = mapped_column(TZDateTime, default=lambda: datetime.now(tz=timezone.utc))
  last_active_at: Mapped[datetime] = mapped_column(
    TZDateTime,
    default=lambda: datetime.now(tz=timezone.utc),
    onupdate=lambda: datetime.now(tz=timezone.utc),
  )
  tier: Mapped[Tier] = mapped_column(IntEnumDecorator(Tier))
  """Used to decide user payment, with tier_lifetime constraints"""
  tier_lifetime: Mapped[datetime | None] = mapped_column(TZDateTime, nullable=True)

  pay_method: Mapped[PayMethod | None] = mapped_column(IntEnumDecorator(PayMethod), nullable=True)
  """Both pay_method & pay_log are auxiliary fields and should not be used to determine payment status"""
  pay_log: Mapped[str] = mapped_column(Text, default="")  # log for payment (success, error, history)
  # currently it's always None because it's always lifelong

  # one user may have 0/multiple invite-codes (in the future>>>). only relationship in ORM level
  invite_codes: Mapped[list["InviteCode"]] = relationship(
    back_populates="bind_user",
    passive_deletes=True,  # Let the db `SET NULL`
  )

  def __str__(self) -> str:
    # no relationship print
    return (
      f"User(id=[{self.id}], email=[{self.email}], created_at=[{safe_strftime(self.created_at)}]"
      f", last_active_at=[{safe_strftime(self.last_active_at)}]"
      f", tier=[{self.tier.name})], lifetime=[{safe_strftime(self.tier_lifetime)}]"
      f", pay_method=[{safe_getattr(self.pay_method, 'name')}]"
      f", pay_log=[{self.pay_log}]"
    )


class InviteCode(DbBaseModel):
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

  bind_user: Mapped[User | None] = relationship(back_populates="invite_codes")

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
      f"InviteCode(id=[{self.id}], code=[{self.code}], lifetime=[{safe_strftime(self.lifetime)}], "
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
