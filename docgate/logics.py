import traceback
import uuid
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from sqlalchemy.orm import Session
from supertokens_python.recipe.emailpassword.types import FormField
from supertokens_python.types import User as StUser

from . import config as config
from .models import InviteCode as InviteCodeModel
from .repositories import create_free_user, create_user_with_redeeming_invite_code, get_db_session_cxt, get_invite_code

logger = config.LOGGER


class InviteCode(object):
  @staticmethod
  def code_len():
    return InviteCodeModel.CODE_LEN

  @staticmethod
  def gen_invite_code():
    """Just use uuid to generate an invite code"""
    code = str(uuid.uuid4()).replace("-", "")[: InviteCode.code_len()]
    return code

  @staticmethod
  def calc_lifetime(base: datetime | None = None) -> datetime:
    EXPIRE_DAYS = 14

    if not base:
      base = datetime.now(tz=timezone.utc)
    return base + timedelta(days=EXPIRE_DAYS)


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
  INVITE_CODE = "invite-code"


class CreateUserStatus(StrEnum):
  # all success
  CREATE_AND_REDEEM_SUCCESS = "Successfully create and redeem user."
  # create user failed
  CREATE_USER_FAILED_ON_SUPERTOKENS_INVALID_USER_DATA = (
    "Create user failed since supertokens don't contain expected user data(.emails is empty)"
  )
  # create user success, while redeem failed
  REDEEM_FAILED_ON_NO_INVITE_CODE_IN_FORM_INPUT = (
    "Redeem failed as form input doesn't contain invite-code, free user created."
  )
  REDEEM_FAILED_ON_INVITE_CODE_NOT_FOUND_IN_DB = (
    "Redeem failed as form input invite-code isn't found in DB, free user created."
  )
  REDEEM_FAILED_ON_INVITE_CODE_NOT_REDEEMABLE = "Redeem failed due to unredeemable invite-code, free user created."
  # internal error. If transaction works, user hasn't been created and code hasn't been redeemed.
  INTERNAL_UNEXPECTED_ERROR = "Internal code unexpected failure, transaction rollback is expected."


def create_user_after_supertokens_signup(user: StUser, form_fields: list[FormField]) -> CreateUserStatus:
  """Create user with redeeming invite-code in our side, after supertokens' sign-up success.
  Exception: No exception, just return the status

  NOTE: If invite-code is invalid, we'll fallback to create a free user without error.
  Used in supertokens post-signup override
  """

  def _logic(db_session: Session) -> CreateUserStatus:
    user_email = user.emails[0]
    invite_code_field: FormField | None = None
    for f in form_fields:
      if f.id == FormFieldId.INVITE_CODE:
        invite_code_field = f
        break
    if invite_code_field is None:
      db_user = create_free_user(db_session, user_id=user.id, email=user_email)
      logger.warning(f"Invite-code: Form field not found! Free user [{db_user}] created.")
      return CreateUserStatus.REDEEM_FAILED_ON_NO_INVITE_CODE_IN_FORM_INPUT
    invite_code_str = invite_code_field.value.strip()
    if not invite_code_str:
      db_user = create_free_user(db_session, user_id=user.id, email=user_email)
      logger.warning(f"Invite-code: From field value is empty! Free user [{db_user}] created.")
      return CreateUserStatus.REDEEM_FAILED_ON_NO_INVITE_CODE_IN_FORM_INPUT
    code_data = get_invite_code(db_session, invite_code_str)
    if not code_data:
      pay_log = f"RedeemInviteCode Fail: code=[{invite_code_str}] wasn't exist in DB"
      db_user = create_free_user(db_session, user_id=user.id, email=user_email, pay_log=pay_log)
      logger.warning(f"{pay_log}. Free user [{db_user}] created.")
      return CreateUserStatus.REDEEM_FAILED_ON_INVITE_CODE_NOT_FOUND_IN_DB
    is_redeemable, reason = code_data.redeemable_with_reason
    if not is_redeemable:
      pay_log = f"RedeemInviteCode Fail: unredeemable code=[{invite_code_str}], reason={reason}"
      db_user = create_free_user(db_session, user_id=user.id, email=user_email, pay_log=pay_log)
      logger.warning(f"{pay_log}. Free user [{db_user}] created.")
      return CreateUserStatus.REDEEM_FAILED_ON_INVITE_CODE_NOT_REDEEMABLE
    db_user = create_user_with_redeeming_invite_code(
      db_session, user_id=user.id, email=user_email, invite_code=code_data
    )
    logger.info(f"RedeemInviteCode Success: redeem code=[{invite_code_str}]. Pay User [{db_user}] created.")
    return CreateUserStatus.CREATE_AND_REDEEM_SUCCESS

  if not user.emails:
    logger.error(f"SuperTokens user doesn't contain emails: {user.to_json()}")
    return CreateUserStatus.CREATE_USER_FAILED_ON_SUPERTOKENS_INVALID_USER_DATA
  try:
    with get_db_session_cxt() as db_session:
      return _logic(db_session)
  except Exception as e:
    logger.error(
      f"Failed to create user with unexpected internal error, user={user.to_json()}. "
      f"err={e}, stack={traceback.format_exc()}"
    )
    return CreateUserStatus.INTERNAL_UNEXPECTED_ERROR
