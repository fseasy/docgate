import traceback
import uuid
from datetime import datetime, timedelta
from enum import StrEnum
from typing import TYPE_CHECKING

from supertokens_python.recipe.emailpassword.types import FormField
from supertokens_python.types import User as StUser

from . import config as config
from .repositories import create_free_user, create_user_with_redeeming_invite_code, get_db_session_cxt, get_invite_code

logger = config.LOGGER


if TYPE_CHECKING:
  from sqlalchemy.orm import Session
  from supertokens_python.recipe.emailpassword.types import FormField


class InviteCode(object):
  @staticmethod
  def code_len():
    INVITE_CODE_LEN = 10
    return INVITE_CODE_LEN

  @staticmethod
  def gen_invite_code():
    """Just use uuid to generate an invite code"""
    code = str(uuid.uuid4()).replace("-", "")[: InviteCode.code_len()]
    return code

  @staticmethod
  def get_lifetime(base: datetime | None = None) -> datetime:
    EXPIRE_DAYS = 14

    if not base:
      base = datetime.now()
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


def create_user_after_supertokens_signup(user: StUser, form_fields: list[FormField]) -> str | None:
  """No exceptions will be thrown. Will return the error string on failure, else nothing on success.
  NOTE: If invite-code is invalid, we'll fallback to create a free user without error.
  Used in supertokens post-signup override
  """

  def _logic(db_session: Session) -> None:
    invite_code_field: FormField | None = None
    for f in form_fields:
      if f.id == FormFieldId.INVITE_CODE:
        invite_code_field = f
        break
    if invite_code_field is None:
      db_user = create_free_user(db_session, user_id=user.id, email=user.emails[0])
      logger.warning("Invite-code: no form field found! Free user [{db_user}] created.")
      return
    invite_code_str = invite_code_field.value
    code_data = get_invite_code(db_session, invite_code_str)
    if not code_data:
      pay_log = f"RedeemInviteCode: failed on not found code: {invite_code_str}"
      db_user = create_free_user(db_session, user_id=user.id, email=user.emails[0], pay_log=pay_log)
      logger.warning(f"{pay_log}. Free user [{db_user}] created.")
      return
    is_redeemable, reason = code_data.redeemable_with_reason
    if not is_redeemable:
      pay_log = f"RedeemInviteCode: failed on unredeemable code: {invite_code_str}, reason={reason}"
      db_user = create_free_user(db_session, user_id=user.id, email=user.emails[0], pay_log=pay_log)
      logger.warning(f"{pay_log}. Free user [{db_user}] created.")
      return
    db_user = create_user_with_redeeming_invite_code(
      db_session, user_id=user.id, email=user.emails[0], invite_code=code_data
    )
    logger.info(f"RedeemInviteCode: redeem code={invite_code_str} success. Pay User [{db_user}] created.")

  try:
    assert user.emails, f"SuperTokens user doesn't contain emails: {user}"
    with get_db_session_cxt() as db_session:
      _logic(db_session)
  except Exception as e:
    err = f"Failed to create user, err={e}, stack={traceback.format_exc()}"
    return err
