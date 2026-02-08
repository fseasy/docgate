import traceback
from typing import Annotated, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.session.asyncio import get_session, refresh_session
from supertokens_python.recipe.session.framework.fastapi import verify_session
from supertokens_python.recipe.userroles import UserRoleClaim

from docgate import config
from docgate.exceptions import InvalidUserInputException, LogicError
from docgate.logics import CreateDbUserLogic, CreateUserStatus, InviteCodeLogic, UserPermissionLogic
from docgate.models import PayLog, Tier
from docgate.repositories import async_create_invite_code, async_get_user, get_db_async_session
from docgate.supertokens_config import StRole
from docgate.supertokens_utils import async_get_user as get_st_user

# We define the routers to group api endpoints and support future expansion.
user_router = APIRouter(prefix="/user", tags=["User"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])
internal_auth_router = APIRouter(prefix="/internal-auth", tags=["InternalAuth"])


logger = config.LOGGER


class StUserResult(BaseModel):
  error: str | None
  user: dict[str, Any] | None


@user_router.get("/get-supertokens-info")
async def get_current_st_user_info(session: SessionContainer = Depends(verify_session())) -> StUserResult:
  uid = session.user_id
  import time

  t = time.perf_counter()
  print(f"Enter get-supertokens-info: {time.perf_counter() - t:.2f}")
  try:
    user = await get_st_user(uid)
    print(f"get get-supertokens-info result: {time.perf_counter() - t:.2f}")
  except Exception as e:
    err = f"[api]: get-supertokens-info fail: uid={uid}, err={e}, stack={traceback.format_exc()}"
    logger.error(f"{err}")
    return StUserResult(error=err, user=None)
  if not user:
    logger.info(f"[api]: get-supertokens-info get None user, uid={uid}")
    return StUserResult(error=None, user=None)
  return StUserResult(error=None, user=user.to_json())


class UserResp(BaseModel):
  id: str
  email: str = "-"
  created_at: str = "-"
  tier: str = "-"
  tier_lifetime: str = "-"
  pay_log: PayLog = Field(default_factory=lambda: PayLog(logs=[]))


@user_router.get("/get")
async def get_current_user_db_info(
  session: SessionContainer = Depends(verify_session()),
  db_session: AsyncSession = Depends(get_db_async_session),
) -> UserResp:
  uid = session.user_id

  user = await async_get_user(db_session, user_id=uid, for_update=False)
  if not user:
    logger.warning(f"[api] get-current-user-db-info: db didn't contain uid: {uid}")
    st_user = await get_st_user(uid)
    if not st_user:
      raise LogicError(f"Neither db nor supertokens contains the user info: {uid}")
    return UserResp(
      id=uid,
      email=st_user.emails[0] if st_user.emails else "-",
      created_at=datetime.fromtimestamp(st_user.time_joined // 1000).isoformat(),
    )
  tier_map = {Tier.FREE: "免费", Tier.GOLD: "付费", Tier.INTERNAL: "内部用户", Tier.INTERNAL_MANAGER: "管理员"}
  return UserResp(
    id=uid,
    email=user.email,
    created_at=user.created_at.isoformat(),
    tier=tier_map[user.tier],
    tier_lifetime=user.tier_lifetime.isoformat() if user.tier_lifetime else "永久",
    pay_log=PayLog.from_db_str(user.pay_log),
  )


class PurchaseByCodeReq(BaseModel):
  invite_code: Annotated[
    str,
    Field(description="invite-code, or pre-pay code"),
    StringConstraints(strip_whitespace=True, min_length=1),
  ]


class PurchaseByCodeResp(BaseModel):
  fail_reason: str | None


@user_router.post("/purchase-by-code")
async def user_purchase_by_code(
  req: PurchaseByCodeReq,
  session: SessionContainer = Depends(verify_session()),
  db_session: AsyncSession = Depends(get_db_async_session),
) -> PurchaseByCodeResp:
  """bind code to user, then add doc-reading permission"""
  uid = session.user_id
  code = req.invite_code
  try:
    db_user = await async_get_user(db_session, user_id=uid, for_update=True)
    if not db_user:
      st_user = await get_st_user(uid)
      if not st_user:
        raise LogicError("Failed to get supertokens user for uid=[uid], which looks impossible")
      await CreateDbUserLogic.async_create_with_redeeming(
        db_session=db_session, user_id=uid, user_email=st_user.emails[0], code_str=code
      )
    else:
      await InviteCodeLogic.binding_db_user(db_session=db_session, db_user=db_user, code=code)
  except InvalidUserInputException as e:
    return PurchaseByCodeResp(fail_reason=e.user_msg)
  except Exception as e:
    err = f"[api]: BindInviteCode get errors: err={e}, stack={traceback.format_exc()}"
    logger.error(f"{err}")
    return PurchaseByCodeResp(fail_reason=err)
  # set permission
  try:
    await UserPermissionLogic.async_set_doc_reading_permission(session, user_id=uid)
  except Exception as e:
    logger.error(f"PurchaseByCode: Failed to set doc-reading permission, err={e}")
    return PurchaseByCodeResp(fail_reason=f"已验证，但权限设置错误，请联系{config.CONTENT_AUTHOR_NAME}")
  return PurchaseByCodeResp(fail_reason=None)


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
    invite_code = InviteCodeLogic.gen_invite_code()
    lifetime = InviteCodeLogic.calc_lifetime()
    await async_create_invite_code(db_session, invite_code, lifetime)
    return InviteResult(error=None, code=invite_code, lifetime=lifetime.strftime("%Y-%m-%d %H:%M:%S %z"))

  try:
    return await _logic()
  except Exception as e:
    return InviteResult(error=str(e), code=None, lifetime=None)


@internal_auth_router.get("/check")
async def docgate_auth_check(request: Request, db_session: AsyncSession = Depends(get_db_async_session)):
  REDIRECT_SESSION_HANDLE_CODE = 401
  REDIRECT_PAY_CODE = 403
  AUTH_PASS_CODE = 200
  import time

  t = time.perf_counter()
  print("enter check, elapsed=", time.perf_counter() - t)

  async def _logic():
    try:
      print("ready request get-session, elapsed=", time.perf_counter() - t)
      session = await get_session(
        request,
        session_required=True,
        anti_csrf_check=False,
      )
      assert session is not None, "`get-session` ok while session result is None"
    except Exception as e:
      print("request get-session failed, elapsed=", time.perf_counter() - t)
      # For all session issue, we give an unified code so that nginx can redirect to an dedicated api
      # => `refresh-session-or-signin`
      logger.info(f"AuthCheck: get exception of [{e}], redirect to session handle")
      return Response(status_code=REDIRECT_SESSION_HANDLE_CODE)
    print("request get-session success, elapsed=", time.perf_counter() - t)
    has_read_permission = await UserPermissionLogic.async_check_doc_reading_permission(session)
    print("request get-user-id success, elapsed=", time.perf_counter() - t)
    if not has_read_permission:
      return Response(status_code=REDIRECT_PAY_CODE)  # redirect to pay
    return Response(status_code=AUTH_PASS_CODE)

  try:
    return await _logic()
  except Exception as e:
    logger.exception(f"AuthCheck: failed due to <{e}>")
    return Response(status_code=500)


@internal_auth_router.get("/refresh-session-or-signin")
async def refresh_session_or_signin(request: Request):
  def _hacking_get_redirect_url():
    """Nginx can only give unquoted redirect url. If we use the request.query_params to get, it may be truncated."""
    DEFAULT_REDIRECT = "/"
    SIG = "s="
    raw_query = request.url.query
    pos = raw_query.lstrip().find(SIG)
    if pos == -1:
      return DEFAULT_REDIRECT
    return raw_query[pos + len(SIG) :]

  redirect_url = _hacking_get_redirect_url()
  print(">>>>>>> REDIRECT path: ", redirect_url)
  try:
    await refresh_session(request)
    logger.info(f"refresh-session: Successfully refresh session, redirect to {redirect_url}")
    return RedirectResponse(url=redirect_url, status_code=302)
  except Exception as e:
    logger.exception(f"refresh-session: Failed to refresh, error={e}")
    return RedirectResponse(url=config.get_st_auth_page_full_url(show="signin", redirect=redirect_url), status_code=302)
