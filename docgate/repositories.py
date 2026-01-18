from contextlib import contextmanager
from datetime import datetime
from typing import Generator

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import InviteCode, PayMethod, SessionLocal, Tier, User


def get_db_session() -> Generator[Session, None, None]:
  """Create a session context. For Fastapi Depends. see: https://fastapi.xiniushu.com/uk/tutorial/sql-databases/"""
  s = SessionLocal()
  try:
    yield s
  finally:
    s.close()


get_db_session_cxt = contextmanager(get_db_session)
"""Used in out-of fastapi scope or place that can't get connection level session"""


def create_user(
  session: Session,
  *,
  user_id: str,
  email: str,
  pay_method: PayMethod | None,
  pay_log: str = "",
  lifetime: datetime | None,
  tier: Tier,
  do_commit: bool = True,
) -> User:
  u = User(id=user_id, email=email, pay_method=pay_method, pay_log=pay_log, lifetime=lifetime, tier=tier)
  session.add(u)
  if do_commit:
    session.commit()
  return u


def create_user_with_redeeming_invite_code(
  session: Session, *, user_id: str, email: str, invite_code: InviteCode, do_commit: bool = True
) -> User:
  """business logic"""
  pay_log = f"Redeem invite-code({invite_code.code})"
  # X with session.begin(): use this may raise exception: A transaction is already begun on this Session.
  user = create_user(
    session,
    user_id=user_id,
    email=email,
    pay_method=PayMethod.INVITE_CODE,
    pay_log=pay_log,
    lifetime=None,
    tier=Tier.GOLD,
    do_commit=False,  # will do final commit
  )
  invite_code.has_used = True
  invite_code.bind_user_id = user_id
  session.add(invite_code)
  if do_commit:
    session.commit()
  return user


def create_free_user(
  session: Session, *, user_id: str, email: str, pay_log: str = "Create without payment", do_commit: bool = True
):
  """Business logic"""
  user = create_user(
    session,
    user_id=user_id,
    email=email,
    pay_method=None,
    pay_log=pay_log,
    lifetime=None,
    tier=Tier.FREE,
    do_commit=do_commit,
  )
  return user


def get_user(session: Session, user_id: str) -> User | None:
  stmt = select(User).where(User.id == user_id)
  u = session.scalar(stmt)
  return u


def create_invite_code(session: Session, code: str, lifetime: datetime, do_commit: bool = True) -> InviteCode:
  code_data = InviteCode(code=code, lifetime=lifetime, has_used=False)
  session.add(code_data)
  if do_commit:
    session.commit()
  return code_data


def get_invite_code(session: Session, code: str) -> InviteCode | None:
  # may be multiple in rare condition, get the latest one
  stmt = select(InviteCode).where(InviteCode.code == code).order_by(InviteCode.lifetime.desc())
  code_data = session.scalars(stmt).first()
  return code_data
