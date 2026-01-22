import traceback
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.cors import CORSMiddleware
from supertokens_python import get_all_cors_headers
from supertokens_python.framework.fastapi import get_middleware
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.session.asyncio import get_session
from supertokens_python.recipe.session.framework.fastapi import verify_session
from supertokens_python.recipe.userroles import UserRoleClaim
from supertokens_python.types import User as StUser

from docgate import config
from docgate.logics import InviteCode, UserPermission
from docgate.models import Tier
from docgate.repositories import async_create_invite_code, async_get_user, get_db_async_session, lifespan_db
from docgate.supertokens_config import StRole, init_supertokens
from docgate.supertokens_utils import async_get_user as get_st_user

logger = config.LOGGER

logger.info("Init Supertokens")
init_supertokens()


logger.info("Build app")
app = FastAPI(title=f"{config.APP_NAME}-backend", lifespan=lifespan_db)

app.add_middleware(get_middleware())

# start apis


class StUserResult(BaseModel):
  error: str | None
  user: dict[str, Any] | None


@app.get("/_docgate/auth_check")
async def docgate_auth_check(request: Request, db_session: AsyncSession = Depends(get_db_async_session)):
  async def _logic():
    session = await get_session(
      request,
      session_required=False,
      anti_csrf_check=False,
    )
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


@app.get("/get_current_supertokens_user")
async def get_current_st_user(session: SessionContainer = Depends(verify_session())) -> StUserResult:
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


@app.post("/gen_invite_code")
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


# after all the apis
app.add_middleware(
  CORSMiddleware,
  allow_origins=[config.WEBSITE_DOMAIN],
  allow_credentials=True,
  allow_methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"],
  allow_headers=["Content-Type"] + get_all_cors_headers(),
)
