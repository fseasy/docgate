import traceback
import uuid
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from supertokens_python.recipe.emailpassword.types import FormField
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.userroles import PermissionClaim, UserRoleClaim
from supertokens_python.types import User as StUser

from docgate.supertokens_config import StRole
from docgate.supertokens_utils import async_add_role2user

from . import config as config
from .exceptions import InvalidUserInputException
from .jwt_verification import AuthJWTPayload
from .models import PayLog, PayLogUnit, PayMethod, PrepaidCode as PrepaidCodeModel, Tier, User
from .repositories import (
  async_create_free_user,
  async_create_paid_user_with_paywall,
  async_create_paid_user_with_redeeming_prepaid_code,
  async_get_prepaid_code,
  async_get_user,
  get_db_async_session_cxt,
)

logger = config.LOGGER


class PaidUserAttr(BaseModel):
  tier: Tier
  tier_lifetime: None  # NOTE: currently only None type. we can use timedelta if necessary
  pay_log_unit: PayLogUnit
  pay_method_raw: PayMethod | None  # used for some api that need the raw value (because pay_log_unit only store str)


class PrepaidCodeLogic(object):
  @staticmethod
  def code_len():
    return PrepaidCodeModel.CODE_LEN

  @staticmethod
  def gen_prepaid_code():
    """Just use uuid to generate an invite code"""
    code = str(uuid.uuid4()).replace("-", "")[: PrepaidCodeLogic.code_len()]
    return code

  @staticmethod
  def calc_lifetime(base: datetime | None = None) -> datetime:
    EXPIRE_DAYS = 14

    if not base:
      base = datetime.now(tz=timezone.utc)
    return base + timedelta(days=EXPIRE_DAYS)

  @staticmethod
  def get_successful_binding_user_attr(code: str) -> PaidUserAttr:
    log = f"预付款码验证成功({code})"
    pay_log_unit = PayLog.create_new_unit(log=log, is_success=True, method=PayMethod.PREPAID_CODE)
    return PaidUserAttr(
      tier=Tier.GOLD, tier_lifetime=None, pay_log_unit=pay_log_unit, pay_method_raw=PayMethod.PREPAID_CODE
    )

  @staticmethod
  async def binding_db_user(db_session: AsyncSession, db_user: User, code: str) -> None:
    """
    Exception:
    - known: InvalidUserInputException: code not exists in db; code isn't redeemable
    - unknown: any
    """
    code_data = await async_get_prepaid_code(db_session, code=code, for_update=True)
    # first check code data
    _check_msg = f"麻烦检查输入无误后联系{config.CONTENT_AUTHOR_NAME}"
    if not code_data:
      log_str = "预付款码不存在"
      db_user.add_paylog(log_str, method=PayMethod.PREPAID_CODE, is_success=False)
      raise InvalidUserInputException(f"code [{code}] not found in db", user_msg=f"{log_str}，{_check_msg}")
    is_redeemable, err_reason = code_data.redeemable_with_reason
    if not is_redeemable:
      log_str = "预付款码已失效"
      db_user.add_paylog(log_str, method=PayMethod.PREPAID_CODE, is_success=False)
      raise InvalidUserInputException(
        f"code [{code}] isn't redeemable, reason={err_reason}", user_msg=f"{log_str}，{_check_msg}"
      )
    code_data.do_binding(db_user.id)
    ua = PrepaidCodeLogic.get_successful_binding_user_attr(code)
    db_user.tier = ua.tier
    db_user.tier_lifetime = ua.tier_lifetime
    log_str = f"验证预付款码成功[{code}]"
    db_user.add_paylog(log_str, method=PayMethod.PREPAID_CODE, is_success=True)
    db_user.last_active_at = datetime.now(tz=timezone.utc)
    db_session.add(code_data)


class PaywallLogic(object):
  @staticmethod
  async def set_db_user_paid(db_session: AsyncSession, user_id: str, email: str) -> None:
    """Exception: any possible"""
    db_user = await async_get_user(db_session, user_id=user_id, for_update=True)
    if not db_user:
      logger.warning(
        "Paywall: set paid user while user not exist in our db. create new!", extra={"user_id": user_id, "email": email}
      )
      await async_create_paid_user_with_paywall(db_session, user_id=user_id, email=email)
      return
    user_attr = PaywallLogic.get_paid_user_attr()
    db_user.tier = user_attr.tier
    db_user.tier_lifetime = user_attr.tier_lifetime
    log = user_attr.pay_log_unit
    db_user.add_paylog(log_str=log.log, method=user_attr.pay_method_raw, is_success=log.is_success)
    db_session.add(db_user)

  @staticmethod
  async def set_db_user_pay_failed(db_session: AsyncSession, user_id: str, email: str) -> None:
    """Add a failed pay log to db user. if user not exist in db, will create 1 free user.
    Exception: any possible"""
    LOG_STR = "自助购买未完成"
    db_user = await async_get_user(db_session, user_id=user_id, for_update=True)
    if not db_user:
      logger.warning(
        "Paywall: set user pay failed while user not exist in our db. create new!",
        extra={"user_id": user_id, "email": email},
      )
      pay_log_unit = PayLog.create_new_unit(log=LOG_STR, method=PayMethod.PAYWALL, is_success=False)
      await async_create_free_user(db_session, user_id=user_id, email=email, pay_log_unit=pay_log_unit)
      return
    db_user.add_paylog(log_str=LOG_STR, method=PayMethod.PAYWALL, is_success=False)
    db_session.add(db_user)

  @staticmethod
  def get_paid_user_attr() -> PaidUserAttr:
    log_unit = PayLog.create_new_unit(log="自助购买", method=PayMethod.PAYWALL, is_success=True)
    return PaidUserAttr(tier=Tier.GOLD, tier_lifetime=None, pay_log_unit=log_unit, pay_method_raw=PayMethod.PAYWALL)


class UserPermissionLogic(object):
  @staticmethod
  def doc_reading_on_db(user: User) -> bool:
    """Outdated strategy. Fetching the user from the database could be very slow (~2s in dev env)
    because of network IO."""
    if user.tier == Tier.FREE:
      return False
    if not user.tier_lifetime:
      # life long
      return True
    return datetime.now(tz=timezone.utc) <= user.tier_lifetime

  @staticmethod
  async def async_check_doc_reading_permission(st_session: SessionContainer) -> bool:
    """Exception: any possible"""
    DOC_READING_ROLES = set([StRole.USER_GOLD_TIER, StRole.ADMIN])

    roles = await st_session.get_claim_value(UserRoleClaim)
    if roles is not None and (set(roles) & DOC_READING_ROLES):
      return True
    return False

  @staticmethod
  async def async_check_doc_reading_permission_jwt(payload: AuthJWTPayload) -> bool:
    """Check if has reading role
    Exception: None
    """
    DOC_READING_ROLES = set([StRole.USER_GOLD_TIER, StRole.ADMIN])
    roles = payload.roles.value if payload.roles else None
    if roles is not None and (set(roles) & DOC_READING_ROLES):
      return True
    return False

  @staticmethod
  async def async_check_email_verified_jwt(payload: AuthJWTPayload) -> bool:
    """Check if email verified
    Exception: None
    """
    if not config.EMAIL_VERIFICATION_REQUIRED:
      return True
    is_email_verified = payload.email_verified.value if payload.email_verified else False
    return is_email_verified

  @staticmethod
  async def async_set_doc_reading_permission(st_session: SessionContainer, user_id: str) -> None:
    """Exception: any possible"""
    add_ok, add_tips = await async_add_role2user(user_id, role=StRole.USER_GOLD_TIER)
    if not add_ok:
      logger.warning(f"SetDocReading permission failed, err={add_tips}", extra={"user_id": user_id})
    await st_session.fetch_and_set_claim(UserRoleClaim)
    await st_session.fetch_and_set_claim(PermissionClaim)


def validate_password(value: str) -> str | None:
  """Return None on success, other return failed reason/tips. Used to override the default supertokens' logic."""

  import re

  if re.search(r"[\s]", value):
    return "Password can't contain whitespace"
  elif len(value) < 4:
    return "Password length should >= 4"
  elif len(value) > 32:
    return "Password length should <= 32"


class FormFieldId(StrEnum):
  PREPAID_CODE = "prepaid-code"


class CreateUserStatus(StrEnum):
  # all success
  CREATE_AND_REDEEM_SUCCESS = "Successfully create and redeem user."
  # create user failed
  CREATE_USER_FAILED_ON_SUPERTOKENS_INVALID_USER_DATA = (
    "Create user failed since supertokens don't contain expected user data(.emails is empty)"
  )
  # create user success, while redeem failed
  REDEEM_FAILED_ON_NO_PREPAID_CODE_IN_FORM_INPUT = (
    "Redeem failed as form input doesn't contain prepaid-code, free user created."
  )
  REDEEM_FAILED_ON_PREPAID_CODE_INVALID = (
    "Redeem failed as form input prepaid-code not found in DB or unredeemable, free user created."
  )
  # internal error. If transaction works, user hasn't been created and code hasn't been redeemed.
  INTERNAL_UNEXPECTED_ERROR = "Internal code unexpected failure, transaction rollback is expected."


class CreateDbUserLogic(object):
  @staticmethod
  async def async_create_with_redeeming(
    db_session: AsyncSession, user_id: str, user_email: str, code_str: str
  ) -> CreateUserStatus:
    """With given code, create user with checking the code. If code is invalid, we'll fallback to create a free user.
    Exception:
    - known: InvalidUserInputException: code not exists in db/ unredeemable
    - unknown: any possible exceptions
    """
    code_data = await async_get_prepaid_code(db_session, code_str, for_update=True)
    if not code_data:
      pay_log_unit = PayLog.create_new_unit(method=PayMethod.PREPAID_CODE, log="预付款码不存在", is_success=False)
      db_user = await async_create_free_user(db_session, user_id=user_id, email=user_email, pay_log_unit=pay_log_unit)
      pay_log_info = f"RedeemCode Fail: code=[{code_str}] wasn't exist in DB"
      logger.warning(f"{pay_log_info}. Free user [{db_user}] created.", extra={"user_id": user_id, "email": user_email})
      raise InvalidUserInputException(pay_log_info, user_msg=pay_log_unit.log)
    is_redeemable, reason = code_data.redeemable_with_reason
    if not is_redeemable:
      pay_log_unit = PayLog.create_new_unit(method=PayMethod.PREPAID_CODE, log="预付款码失效", is_success=False)
      db_user = await async_create_free_user(db_session, user_id=user_id, email=user_email, pay_log_unit=pay_log_unit)
      pay_log_info = f"RedeemCode Fail: unredeemable code=[{code_str}], reason={reason}"
      logger.warning(f"{pay_log_info}. Free user [{db_user}] created.", extra={"user_id": user_id, "email": user_email})
      raise InvalidUserInputException(pay_log_info, user_msg=pay_log_unit.log)
    db_user = await async_create_paid_user_with_redeeming_prepaid_code(
      db_session, user_id=user_id, email=user_email, prepaid_code=code_data
    )
    logger.info(
      f"RedeemCode Success: redeem code=[{code_str}]. Paid user [{db_user}] created.",
      extra={"user_id": user_id, "email": user_email},
    )
    return CreateUserStatus.CREATE_AND_REDEEM_SUCCESS

  @staticmethod
  async def async_create_after_supertokens_signup(user: StUser, form_fields: list[FormField]) -> CreateUserStatus:
    """Create user with redeeming prepaid-code in our side, after supertokens' sign-up success.
    Exception: No exception, just return the status

    Used in supertokens post-signup override.

    NOTE: If prepaid-code is invalid, we'll fallback to create a free user without error.
    """

    async def _logic(db_session: AsyncSession) -> CreateUserStatus:
      user_email = user.emails[0]
      prepaid_code_field: FormField | None = None
      for f in form_fields:
        if f.id == FormFieldId.PREPAID_CODE:
          prepaid_code_field = f
          break
      if prepaid_code_field is None:
        pay_log_unit = PayLog.create_new_unit(method=None, log="无支付", is_success=False)
        db_user = await async_create_free_user(db_session, user_id=user.id, email=user_email, pay_log_unit=pay_log_unit)
        logger.warning(
          f"Code: Form field not found! Free user [{db_user}] created.", extra={"user_id": user.id, "email": user_email}
        )
        return CreateUserStatus.REDEEM_FAILED_ON_NO_PREPAID_CODE_IN_FORM_INPUT
      prepaid_code_str = prepaid_code_field.value.strip()
      if not prepaid_code_str:
        pay_log_unit = PayLog.create_new_unit(method=None, log="无支付", is_success=False)
        db_user = await async_create_free_user(db_session, user_id=user.id, email=user_email, pay_log_unit=pay_log_unit)
        logger.warning(
          f"Code: From field value is empty! Free user [{db_user}] created.",
          extra={"user_id": user.id, "email": user_email},
        )
        return CreateUserStatus.REDEEM_FAILED_ON_NO_PREPAID_CODE_IN_FORM_INPUT
      return await CreateDbUserLogic.async_create_with_redeeming(
        db_session=db_session, user_id=user.id, user_email=user_email, code_str=prepaid_code_str
      )

    if not user.emails:
      logger.error(f"SuperTokens user doesn't contain emails: {user.to_json()}", extra={"user_id": user.id})
      return CreateUserStatus.CREATE_USER_FAILED_ON_SUPERTOKENS_INVALID_USER_DATA
    try:
      async with get_db_async_session_cxt() as db_session:
        return await _logic(db_session)
    except InvalidUserInputException:
      return CreateUserStatus.REDEEM_FAILED_ON_PREPAID_CODE_INVALID
    except Exception as e:
      logger.error(
        f"Failed to create user with unexpected internal error, user={user.to_json()}. "
        f"err={e}, stack={traceback.format_exc()}",
        extra={"user_id": user.id, "email": user.emails[0]},
      )
      return CreateUserStatus.INTERNAL_UNEXPECTED_ERROR
