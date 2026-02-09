from contextlib import asynccontextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Any, AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
  AsyncSessionLocal,
  PayLog,
  PayLogUnit,
  PayMethod,
  PrepaidCode,
  Tier,
  User,
  create_all_tables,
  dispose_engine,
)

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
  pay_log: PayLog,
  tier_lifetime: datetime | None,
  tier: Tier,
  do_commit: bool = False,
) -> User:
  u = User(id=user_id, email=email, tier=tier, tier_lifetime=tier_lifetime, pay_log=pay_log.to_db_str())
  session.add(u)
  if do_commit:
    await session.commit()
  return u


async def async_create_paid_user_with_redeeming_prepaid_code(
  session: AsyncSession, *, user_id: str, email: str, prepaid_code: PrepaidCode, do_commit: bool = False
) -> User:
  """business logic"""
  from .logics import PrepaidCodeLogic as ICLogic

  user_bind_attr = ICLogic.get_successful_binding_user_attr(prepaid_code.code)
  pay_log = PayLog(logs=[user_bind_attr.pay_log_unit])
  # !NOTE: don't `with session.begin():`
  # use this may raise exception: A transaction is already begun on this Session.
  # because currently a request will automatically build a transaction. here is already inside a transaction
  user = await async_create_user(
    session,
    user_id=user_id,
    email=email,
    tier=user_bind_attr.tier,
    tier_lifetime=user_bind_attr.tier_lifetime,
    pay_log=pay_log,
    do_commit=False,  # will do final commit
  )
  prepaid_code.do_binding(user_id)
  session.add(prepaid_code)
  if do_commit:
    await session.commit()
  return user


async def async_create_paid_user_with_paywall(
  session: AsyncSession, *, user_id: str, email: str, do_commit: bool = False
) -> User:
  """business logic"""
  from .logics import PaywallLogic

  user_attr = PaywallLogic.get_paid_user_attr()
  pay_log = PayLog(logs=[user_attr.pay_log_unit])
  user = await async_create_user(
    session,
    user_id=user_id,
    email=email,
    tier=user_attr.tier,
    tier_lifetime=user_attr.tier_lifetime,
    pay_log=pay_log,
    do_commit=False,  # will do final commit
  )
  if do_commit:
    await session.commit()
  return user


async def async_create_free_user(
  session: AsyncSession, *, user_id: str, email: str, pay_log_unit: PayLogUnit, do_commit: bool = False
):
  """Business logic"""
  user = await async_create_user(
    session,
    user_id=user_id,
    email=email,
    tier=Tier.FREE,
    tier_lifetime=None,
    pay_log=PayLog(logs=[pay_log_unit]),
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
  await session.delete(u)  # will unbind prepaid-codes user id.


async def async_create_prepaid_code(
  session: AsyncSession, code: str, lifetime: datetime, do_commit: bool = False
) -> PrepaidCode:
  assert lifetime.tzinfo, f"Lifetime tzinfo is None in lifetime: {lifetime}"
  code_data = PrepaidCode(code=code, lifetime=lifetime, has_used=False)
  session.add(code_data)
  if do_commit:
    await session.commit()
  return code_data


async def async_get_prepaid_code(session: AsyncSession, code: str, for_update: bool = False) -> PrepaidCode | None:
  """
  Args:
  - for_update: if True, will lock the row to avoid race-condition
  """
  # may be multiple in rare condition, get the latest one
  stmt = select(PrepaidCode).where(PrepaidCode.code == code).order_by(PrepaidCode.lifetime.desc())
  if for_update:
    stmt = stmt.with_for_update()  # LOCK
  r = await session.execute(stmt)
  code_data = r.scalars().first()
  return code_data
