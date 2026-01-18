from datetime import datetime, timezone
from enum import IntEnum, StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from .logics import InviteCode as InviteCodeLogic
from .utils import safe_getattr

if TYPE_CHECKING:
  from sqlalchemy.engine import Engine


# Define enums
class PayMethod(StrEnum):
  INVITE_CODE = "invite_code"
  SELF_HOSTED_PAYWALL = "self_hosted_paywall"


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

# Session maker instance
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)


class DbBaseModel(DeclarativeBase):
  pass


class User(DbBaseModel):
  __tablename__ = "users"

  id: Mapped[str] = mapped_column(String(36), primary_key=True)  # for external user id
  email: Mapped[str] = mapped_column(String(100), index=True)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), insert_default=func.now)
  last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), insert_default=func.now)
  pay_method: Mapped[PayMethod | None] = mapped_column(Integer(), nullable=True)
  pay_log: Mapped[str] = mapped_column(Text, default="")  # log for payment (success, error, history)
  # currently it's always None because it's always lifelong
  lifetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
  tier: Mapped[Tier] = mapped_column(Integer())

  # one user may have 0/multiple invite-codes (in the future>>>). only relationship in ORM level
  invite_codes: Mapped[list["InviteCode"]] = relationship(back_populates="bind_user")

  def __str__(self) -> str:
    # no relationship print
    return (
      f"User(id={self.id}, email={self.email}, created_at={self.created_at}"
      f", last_active_at={self.last_active_at}, pay_method={safe_getattr(self.pay_method, 'name')}"
      f", pay_log={self.pay_log}, lifetime={self.lifetime}, tier={self.tier.name})"
    )


class InviteCode(DbBaseModel):
  __tablename__ = "invite_codes"

  id: Mapped[int] = mapped_column(primary_key=True)
  code: Mapped[str] = mapped_column(String(InviteCodeLogic.code_len()), index=True)
  lifetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
  has_used: Mapped[bool] = mapped_column(Boolean(), default=False)
  bind_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, default=None)

  bind_user: Mapped[User | None] = relationship(back_populates="invite_codes")

  @property
  def redeemable_with_reason(self) -> tuple[bool, str | None]:
    if self.has_used:
      return (False, f"code={self} has already been used")
    if datetime.now(timezone.utc) > self.lifetime:
      return (False, f"code={self} has expired(lifetime={self.lifetime})")
    return (True, None)

  def __str__(self) -> str:
    # no relationship print
    return (
      f"InviteCode(id={self.id}, code={self.code}, lifetime={self.lifetime}, "
      f"has_used={self.has_used}, bind_user_id={self.bind_user_id})"
    )


def _init_db():
  DbBaseModel.metadata.create_all(engine)


_init_db()  # We call init db here so it's self-contained
