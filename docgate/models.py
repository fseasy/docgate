from datetime import datetime, timezone
from enum import IntEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, TypeDecorator, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from .config import LOGGER as logger
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


def _get_sqlite_db_path() -> str:
  from pathlib import Path

  _workspace_dir = Path(__file__).parent
  p = f"sqlite:///{_workspace_dir / 'sqlite.db'}"
  return p


async_engine = create_async_engine(_get_sqlite_db_path(), connect_args={"check_same_thread": False})

# Session maker instance
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)


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
  """Save & Load always keep the UTC tz. (sqlite didn't reserve the tz info, which may error-prone)"""

  impl = DateTime  # lower type
  cache_ok = True  # allow SQLAlchemy cache

  def process_bind_param(self, value, dialect):
    """when bind outer value"""
    if value is None:
      return None
    if value.tzinfo is None:
      value = value.replace(tzinfo=timezone.utc)
    else:
      value = value.astimezone(timezone.utc)
    return value

  def process_result_value(self, value, dialect):
    """when read from dialect db"""
    if value is None:
      return None
    if value.tzinfo is None:  # 1. no tz 2. tz = utc
      return value.replace(tzinfo=timezone.utc)
    return value


class DbBaseModel(DeclarativeBase):
  pass


class User(DbBaseModel):
  __tablename__ = "users"

  id: Mapped[str] = mapped_column(String(36), primary_key=True)  # for external user id
  email: Mapped[str] = mapped_column(String(100), index=True)
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
  invite_codes: Mapped[list["InviteCode"]] = relationship(back_populates="bind_user")

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
  __tablename__ = "invite_codes"

  CODE_LEN = 10

  id: Mapped[int] = mapped_column(primary_key=True)
  code: Mapped[str] = mapped_column(String(CODE_LEN), index=True)
  lifetime: Mapped[datetime] = mapped_column(TZDateTime)
  has_used: Mapped[bool] = mapped_column(Boolean(), default=False)
  bind_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, default=None)

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


def _init_db():
  DbBaseModel.metadata.create_all(engine)


_init_db()  # We call init db here so it's self-contained
