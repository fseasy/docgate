from enum import  StrEnum, IntEnum
from datetime import datetime, timezone

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import create_engine

# Define enums
class PayMethod(StrEnum):
  RED_NOTE = "RED_NOTE"
  SELF_HOSTED_PAYWALL = "self_hosted_paywall"


class Tier(IntEnum):
  INTERNAL_MANAGER = 0
  INTERNAL = 1
  NORMAL_CUSTOMER = 2


class Base(DeclarativeBase):
  pass


class User(Base):
  __tablename__ = "users"

  uid: Mapped[str] = mapped_column(String(36), primary_key=True)
  create_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
  last_active_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
  pay_method: Mapped[PayMethod] = mapped_column(String(36))
  lifetime: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
  tier: Mapped[Tier] = mapped_column(Integer())


def _create_sqlite_engine():
  from pathlib import Path

  _workspace_dir = Path(__file__).parent
  DB_PATH = f"sqlite:///{_workspace_dir / 'sqlite.db'}"
  engine = create_engine(DB_PATH, echo=True)
  return engine


engine = _create_sqlite_engine()