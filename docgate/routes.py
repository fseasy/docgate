import traceback
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.session.asyncio import get_session, refresh_session
from supertokens_python.recipe.session.framework.fastapi import verify_session
from supertokens_python.recipe.userroles import UserRoleClaim

from docgate import config
from docgate.exceptions import InvalidUserInputException, LogicError
from docgate.logics import CreateDbUserLogic, PrepaidCodeLogic, UserPermissionLogic
from docgate.models import PayLog
from docgate.repositories import async_create_prepaid_code, async_get_user, get_db_async_session
from docgate.supertokens_config import StRole
from docgate.supertokens_utils import (
  async_create_password_reset_link,
  async_get_user as get_st_user,
  async_manually_verify_email,
)
from docgate.jwt_verification import verify_jwt

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
    logger.error(f"{err}", extra={"user_id": uid})
    return StUserResult(error=err, user=None)
  if not user:
    logger.info(f"[api]: get-supertokens-info get None user, uid={uid}", extra={"user_id": uid})
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
    logger.warning(f"[api] get-current-user-db-info: db didn't contain uid: {uid}", extra={"user_id": uid})
    st_user = await get_st_user(uid)
    if not st_user:
      raise LogicError(f"Neither db nor supertokens contains the user info: {uid}")
    return UserResp(
      id=uid,
      email=st_user.emails[0] if st_user.emails else "-",
      created_at=datetime.fromtimestamp(st_user.time_joined // 1000).isoformat(),
    )
  return UserResp(
    id=uid,
    email=user.email,
    created_at=user.created_at.isoformat(),
    tier=user.tier.locale_name(),
    tier_lifetime=user.tier_lifetime.isoformat() if user.tier_lifetime else "永久",
    pay_log=PayLog.from_db_str(user.pay_log),
  )


class PurchaseByCodeReq(BaseModel):
  prepaid_code: Annotated[
    str,
    Field(description="prepaid-code, or pre-pay code"),
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
  code = req.prepaid_code
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
      await PrepaidCodeLogic.binding_db_user(db_session=db_session, db_user=db_user, code=code)
  except InvalidUserInputException as e:
    return PurchaseByCodeResp(fail_reason=e.user_msg)
  except Exception as e:
    err = f"[api]: BindPrepaidCode get errors: err={e}, stack={traceback.format_exc()}"
    logger.error(f"{err}", extra={"user_id": uid, "code": code})
    return PurchaseByCodeResp(fail_reason=err)
  # set permission
  assert db_user
  try:
    await UserPermissionLogic.async_set_doc_reading_permission(session, user_id=uid)
  except Exception as e:
    logger.error(
      f"PurchaseByCode: Failed to set doc-reading permission, err={e}",
      extra={"user_id": uid, "email": db_user.email, "code": code},
    )
    return PurchaseByCodeResp(fail_reason=f"已验证，但权限设置错误，请联系{config.CONTENT_AUTHOR_NAME}")
  return PurchaseByCodeResp(fail_reason=None)


class GenPrepaidCodeResp(BaseModel):
  error: str | None
  code: str | None
  lifetime: str | None


@admin_router.post("/gen-prepaid-code")
async def gen_prepaid_code(
  session: SessionContainer = Depends(verify_session()), db_session: AsyncSession = Depends(get_db_async_session)
) -> GenPrepaidCodeResp:
  """generate prepaid-code, record it to table"""

  async def _logic():
    user_id = session.get_user_id()
    # We use Supertokens' User Role to control the permission
    roles = await session.get_claim_value(UserRoleClaim)
    if roles is None or StRole.ADMIN not in roles:
      return GenPrepaidCodeResp(
        error=f"user [{user_id}] didn't have admin role. roles={roles}", code=None, lifetime=None
      )
    prepaid_code = PrepaidCodeLogic.gen_prepaid_code()
    lifetime = PrepaidCodeLogic.calc_lifetime()
    await async_create_prepaid_code(db_session, prepaid_code, lifetime)
    return GenPrepaidCodeResp(error=None, code=prepaid_code, lifetime=lifetime.strftime("%Y-%m-%d %H:%M:%S %z"))

  try:
    return await _logic()
  except Exception as e:
    return GenPrepaidCodeResp(error=str(e), code=None, lifetime=None)


class CreatePasswordResetLinkReq(BaseModel):
  email: Annotated[
    str,
    Field(description="user email"),
    StringConstraints(strip_whitespace=True, min_length=1),
  ]


class CreatePasswordResetLinkResp(BaseModel):
  is_success: bool
  link: str | None
  fail_reason: str | None


@admin_router.post("/create-password-reset-link")
async def create_password_reset_link(
  req: CreatePasswordResetLinkReq,
  session: SessionContainer = Depends(verify_session()),
) -> CreatePasswordResetLinkResp:
  """create password reset link for a given email"""

  async def _logic():
    user_id = session.get_user_id()
    roles = await session.get_claim_value(UserRoleClaim)
    if roles is None or StRole.ADMIN not in roles:
      return CreatePasswordResetLinkResp(
        is_success=False, link=None, fail_reason=f"user [{user_id}] didn't have admin role. roles={roles}"
      )
    result = await async_create_password_reset_link(req.email)
    return CreatePasswordResetLinkResp(is_success=result.is_success, link=result.link, fail_reason=result.fail_reason)

  try:
    return await _logic()
  except Exception as e:
    return CreatePasswordResetLinkResp(is_success=False, link=None, fail_reason=str(e))


class ManuallyVerifyEmailReq(BaseModel):
  email: Annotated[
    str,
    Field(description="user email"),
    StringConstraints(strip_whitespace=True, min_length=1),
  ]


class ManuallyVerifyEmailResp(BaseModel):
  is_success: bool
  fail_reason: str | None


@admin_router.post("/manually-verify-email")
async def manually_verify_email(
  req: ManuallyVerifyEmailReq,
  session: SessionContainer = Depends(verify_session()),
) -> ManuallyVerifyEmailResp:
  """manually verify email for a given email"""

  async def _logic():
    user_id = session.get_user_id()
    roles = await session.get_claim_value(UserRoleClaim)
    if roles is None or StRole.ADMIN not in roles:
      return ManuallyVerifyEmailResp(
        is_success=False, fail_reason=f"user [{user_id}] didn't have admin role. roles={roles}"
      )
    is_success, fail_reason = await async_manually_verify_email(req.email)
    return ManuallyVerifyEmailResp(is_success=is_success, fail_reason=fail_reason)

  try:
    return await _logic()
  except Exception as e:
    return ManuallyVerifyEmailResp(is_success=False, fail_reason=str(e))


@internal_auth_router.get("/check")
async def docgate_auth_check(request: Request):
  """We give up calling supertokens `get_session` due to it's unpreventable core request. Use local jwt instead
  Following the doc: https://supertokens.com/docs/additional-verification/session-verification/\
                     protect-api-routes#using-a-jwt-verification-library
  """
  REDIRECT_SESSION_HANDLE_CODE = 401
  REDIRECT_PAY_CODE = 403
  AUTH_PASS_CODE = 200
  import time

  async def _logic():
    t = time.perf_counter()
    token = request.cookies.get("sAccessToken")
    try:
      if not token:
        raise Exception("No sAccessToken token in Cookies")
      access_payload = await verify_jwt(token)
    except Exception as e:
      # For all session issue, we give an unified code so that nginx can redirect to an dedicated api
      # => `refresh-session-or-signin`
      logger.info(
        f"AuthCheck: get exception of [{e}], redirect to session handle",
        extra={"get_payload_time_cost": round(time.perf_counter() - t, 4)},
      )
      return Response(status_code=REDIRECT_SESSION_HANDLE_CODE)

    logger.info(
      "AuthCheck get-payload success",
      extra={"get_payload_time_cost": round(time.perf_counter() - t, 4), "user_id": access_payload.user_id},
    )
    if not await UserPermissionLogic.async_check_email_verified_jwt(access_payload):
      logger.info("AuthCheck fail, email not verified", extra={"user_id": access_payload.user_id})
      return Response(status_code=REDIRECT_SESSION_HANDLE_CODE)
    # zero io cost for `async_check_doc_reading_permission`
    has_read_permission = await UserPermissionLogic.async_check_doc_reading_permission_jwt(access_payload)
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
  try:
    await refresh_session(request)
    logger.info(f"refresh-session: Successfully refresh session, redirect to {redirect_url}")
    return RedirectResponse(url=redirect_url, status_code=302)
  except Exception as e:
    logger.exception(f"refresh-session: Failed to refresh, error={e}")
    return RedirectResponse(url=config.get_st_auth_page_full_url(show="signin", redirect=redirect_url), status_code=302)
