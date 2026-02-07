from contextlib import asynccontextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Any, AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AsyncSessionLocal, InviteCode, PayMethod, Tier, User, create_all_tables, dispose_engine

if TYPE_CHECKING:
  from fastapi import FastAPI


async def get_db_async_session() -> AsyncGenerator[AsyncSession, Any]:
  """Get a database session.
  To be used for dependency injection.
  copy from: https://github.com/seapagan/fastapi_async_sqlalchemy2_example/blob/main/db.py#L42
  """
  async with AsyncSessionLocal() as session, session.begin():
    yield session


get_db_async_session_cxt = asynccontextmanager(get_db_async_session)
"""Used in out-of fastapi scope or place that can't get connection level session"""


@asynccontextmanager
async def lifespan_db(_: "FastAPI | None") -> AsyncGenerator[Any, None]:
  await create_all_tables()  # create tables if eligible
  yield
  await dispose_engine()  # dispose db after app close!


async def async_create_user(
  session: AsyncSession,
  *,
  user_id: str,
  email: str,
  pay_method: PayMethod | None,
  pay_log: str = "",
  tier_lifetime: datetime | None,
  tier: Tier,
  do_commit: bool = False,
) -> User:
  u = User(id=user_id, email=email, tier=tier, tier_lifetime=tier_lifetime, pay_method=pay_method, pay_log=pay_log)
  session.add(u)
  if do_commit:
    await session.commit()
  return u


async def async_create_user_with_redeeming_invite_code(
  session: AsyncSession, *, user_id: str, email: str, invite_code: InviteCode, do_commit: bool = False
) -> User:
  """business logic"""
  from .logics import InviteCode as ICLogic

  user_bind_attr = ICLogic.get_bind_user_attr(invite_code.code)
  # X with session.begin(): use this may raise exception: A transaction is already begun on this Session.
  user = await async_create_user(
    session,
    user_id=user_id,
    email=email,
    tier=user_bind_attr.tier,
    tier_lifetime=user_bind_attr.tier_lifetime,
    pay_method=user_bind_attr.pay_method,
    pay_log=user_bind_attr.pay_log,
    do_commit=False,  # will do final commit
  )
  invite_code.do_binding(user_id)
  session.add(invite_code)
  if do_commit:
    await session.commit()
  return user


async def async_create_free_user(
  session: AsyncSession, *, user_id: str, email: str, pay_log: str = "Create without payment", do_commit: bool = False
):
  """Business logic"""
  user = await async_create_user(
    session,
    user_id=user_id,
    email=email,
    tier=Tier.FREE,
    tier_lifetime=None,
    pay_method=None,
    pay_log=pay_log,
    do_commit=do_commit,
  )
  return user


async def async_get_user(session: AsyncSession, user_id: str, for_update: bool = False) -> User | None:
  stmt = select(User).where(User.id == user_id)
  if for_update:
    stmt = stmt.with_for_update()
  r = await session.execute(stmt)
  u = r.scalar()
  return u


async def async_delete_user(session: AsyncSession, user_id: str) -> str | None:
  """Return error string on failure, else return None. Exception wont't be catch."""
  u = await async_get_user(session, user_id)
  if not u:
    return f"Delete user(id={user_id}) failed due to it doesn't exist in our db"
  await session.delete(u)  # will unbind invite-codes user id.


async def async_create_invite_code(
  session: AsyncSession, code: str, lifetime: datetime, do_commit: bool = False
) -> InviteCode:
  assert lifetime.tzinfo, f"Lifetime tzinfo is None in lifetime: {lifetime}"
  code_data = InviteCode(code=code, lifetime=lifetime, has_used=False)
  session.add(code_data)
  if do_commit:
    await session.commit()
  return code_data


async def async_get_invite_code(session: AsyncSession, code: str, for_update: bool = False) -> InviteCode | None:
  """
  Args:
  - for_update: if True, will lock the row to avoid race-condition
  """
  # may be multiple in rare condition, get the latest one
  stmt = select(InviteCode).where(InviteCode.code == code).order_by(InviteCode.lifetime.desc())
  if for_update:
    stmt = stmt.with_for_update()  # LOCK
  r = await session.execute(stmt)
  code_data = r.scalars().first()
  return code_data
