import traceback
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.session.asyncio import get_session
from supertokens_python.recipe.session.exceptions import TryRefreshTokenError, UnauthorisedError
from supertokens_python.recipe.session.framework.fastapi import verify_session
from supertokens_python.recipe.userroles import UserRoleClaim

from docgate import config
from docgate.logics import InviteCode, UserPermission
from docgate.repositories import async_create_invite_code, async_get_user, get_db_async_session
from docgate.supertokens_config import StRole
from docgate.supertokens_utils import async_get_user as get_st_user

# We define the routers to group api endpoints and support future expansion.
user_router = APIRouter(prefix="/user", tags=["User"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])
internal_auth_router = APIRouter(prefix="/internal_auth", tags=["InternalAuth"])


logger = config.LOGGER


class StUserResult(BaseModel):
  error: str | None
  user: dict[str, Any] | None


@user_router.get("/get-supertokens-info")
async def get_current_st_user_info(session: SessionContainer = Depends(verify_session())) -> StUserResult:
  uid = session.user_id
  try:
    user = await get_st_user(uid)
  except Exception as e:
    err = f"[api]: GetUserEmails get errors: uid={uid}, err={e}, stack={traceback.format_exc()}"
    logger.error(f"{err}")
    return StUserResult(error=err, user=None)
  if not user:
    logger.info(f"[api]: GetUserEmails get None user, uid={uid}")
    return StUserResult(error=None, user=None)
  return StUserResult(error=None, user=user.to_json())


class InviteResult(BaseModel):
  error: str | None
  code: str | None
  lifetime: str | None


@admin_router.post("/gen-invite-code")
async def gen_invite(
  session: SessionContainer = Depends(verify_session()), db_session: AsyncSession = Depends(get_db_async_session)
) -> InviteResult:
  """generate invite-code, record it to table"""

  async def _logic():
    user_id = session.get_user_id()
    # We use Supertokens' User Role to control the permission
    roles = await session.get_claim_value(UserRoleClaim)
    if roles is None or StRole.ADMIN not in roles:
      return InviteResult(error=f"user [{user_id}] didn't have admin role. roles={roles}", code=None, lifetime=None)
    invite_code = InviteCode.gen_invite_code()
    lifetime = InviteCode.calc_lifetime()
    await async_create_invite_code(db_session, invite_code, lifetime)
    return InviteResult(error=None, code=invite_code, lifetime=lifetime.strftime("%Y-%m-%d %H:%M:%S %z"))

  try:
    return await _logic()
  except Exception as e:
    return InviteResult(error=str(e), code=None, lifetime=None)


@internal_auth_router.get("/check")
async def docgate_auth_check(request: Request, db_session: AsyncSession = Depends(get_db_async_session)):
  async def _logic():
    try:
      session = await get_session(
        request,
        session_required=True,
        anti_csrf_check=False,
      )
    except TryRefreshTokenError:
      return Response(status_code=401)  # let the frontend sdk handle (refresh token if possible)
    except UnauthorisedError:
      return Response(status_code=401)  # let the frontend sdk handle
    except Exception:
      return Response(status_code=401)  # we can return 500 if aggressively. But we don't need to do this.
    if session is None:
      return Response(status_code=401)  # redirect to signup
    user_id = session.get_user_id()
    user = await async_get_user(db_session, user_id)
    if user is None:
      # ! this is the system inconsistency. we just redirect to pay, once customer pay, we can insert it to our db.
      return Response(status_code=403)  # redirect to pay
    if not UserPermission.can_read_doc(user):
      return Response(status_code=403)  # redirect to pay
    # pass
    return Response(status_code=200)

  try:
    return await _logic()
  except Exception as e:
    logger.exception(f"docgate-auth-check failed due to <{e}>")
    return Response(status_code=500)
