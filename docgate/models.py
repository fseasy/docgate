from datetime import datetime, timezone
from enum import IntEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, TypeDecorator, create_engine
from sqlalchemy.engine import Engine
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


def _create_sqlite_engine() -> Engine:
  from pathlib import Path

  _workspace_dir = Path(__file__).parent
  DB_PATH = f"sqlite:///{_workspace_dir / 'sqlite.db'}"
  return create_engine(DB_PATH, connect_args={"check_same_thread": False})


engine = _create_sqlite_engine()
"""DB Engine"""

# Session maker instance
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)


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


class DbBaseModel(DeclarativeBase):
  pass


class User(DbBaseModel):
  __tablename__ = "users"

  id: Mapped[str] = mapped_column(String(36), primary_key=True)  # for external user id
  email: Mapped[str] = mapped_column(String(100), index=True)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc))
  last_active_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    default=lambda: datetime.now(tz=timezone.utc),
    onupdate=lambda: datetime.now(tz=timezone.utc),
  )

  pay_method: Mapped[PayMethod | None] = mapped_column(IntEnumDecorator(PayMethod), nullable=True)
  """
  Config explain:
  native_num=False, don't use SQL's enum; create_constraint=False, dont' generate constraints in SQL;
  values_callable=lambda: use the value(int) instead of the name(str) of the enum
  All is for easily extend the enum while keep it sufficient in DB and Python side.
  """

  pay_log: Mapped[str] = mapped_column(Text, default="")  # log for payment (success, error, history)
  # currently it's always None because it's always lifelong
  lifetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
  tier: Mapped[Tier] = mapped_column(IntEnumDecorator(Tier))

  # one user may have 0/multiple invite-codes (in the future>>>). only relationship in ORM level
  invite_codes: Mapped[list["InviteCode"]] = relationship(back_populates="bind_user")

  def __str__(self) -> str:
    # no relationship print
    return (
      f"User(id=[{self.id}], email=[{self.email}], created_at=[{safe_strftime(self.created_at)}]"
      f", last_active_at=[{safe_strftime(self.last_active_at)}]"
      f", pay_method=[{safe_getattr(self.pay_method, 'name')}]"
      f", pay_log=[{self.pay_log}], lifetime=[{safe_strftime(self.lifetime)}], tier=[{self.tier.name})]"
    )


class InviteCode(DbBaseModel):
  __tablename__ = "invite_codes"

  CODE_LEN = 10

  id: Mapped[int] = mapped_column(primary_key=True)
  code: Mapped[str] = mapped_column(String(CODE_LEN), index=True)
  lifetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
  has_used: Mapped[bool] = mapped_column(Boolean(), default=False)
  bind_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, default=None)

  bind_user: Mapped[User | None] = relationship(back_populates="invite_codes")

  @property
  def redeemable_with_reason(self) -> tuple[bool, str | None]:
    if self.has_used:
      return (False, f"code={self} has already been used")
    lifetime = self.lifetime
    if lifetime.tzinfo is None:
      logger.warning("DB InviteCode: read `lifetime` doesn't contain tz info. add UTC as fallback")
      lifetime = lifetime.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > lifetime:
      return (False, f"code={self} has expired(lifetime={self.lifetime})")
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
