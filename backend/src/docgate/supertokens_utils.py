from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel
from supertokens_python.recipe.emailpassword.asyncio import create_reset_password_link
from supertokens_python.recipe.emailverification.asyncio import (
  create_email_verification_token,
  verify_email_using_token,
)
from supertokens_python.recipe.emailverification.interfaces import CreateEmailVerificationTokenOkResult
from supertokens_python.recipe.userroles.asyncio import add_role_to_user, create_new_role_or_add_permissions
from supertokens_python.recipe.userroles.interfaces import UnknownRoleError
from supertokens_python.types import RecipeUserId, User

from . import config as base_conf
from .supertokens_config import StRole

if TYPE_CHECKING:
  from supertokens_python.recipe.session.interfaces import SessionClaimValidator, SessionContainer

logger = base_conf.LOGGER


async def async_delete_user(user_id: str) -> None:
  from supertokens_python.asyncio import delete_user

  return await delete_user(user_id=user_id)


async def async_get_user(user_id: str) -> User | None:
  from supertokens_python.asyncio import get_user

  return await get_user(user_id)


async def async_get_user_by_email(email: str) -> list[User]:
  from supertokens_python.asyncio import list_users_by_account_info
  from supertokens_python.types.base import AccountInfoInput

  return await list_users_by_account_info("public", AccountInfoInput(email=email))


async def async_add_role2user(user_id: str, role: StRole) -> tuple[bool, str | None]:
  """
  Returns:
    (is_success, tips)
    tips: Return None if all success, else return error/warning info"""
  res = await add_role_to_user("public", user_id, role)
  if isinstance(res, UnknownRoleError):
    return (False, f"Unknown role, err={res}")
  if res.did_user_already_have_role:
    return (True, f"User {user_id} already has role of {role}")
  return (True, None)


async def async_init_roles() -> None:
  """NOTE: you can only create role on yourself environment. i.e., you can't create role in the `try.supertokens.io`"""
  logger.info("Init supertokens roles")

  user_res = create_new_role_or_add_permissions(StRole.USER, [])
  user_gold_res = create_new_role_or_add_permissions(StRole.USER_GOLD_TIER, ["read"])
  admin_res = create_new_role_or_add_permissions(StRole.ADMIN, ["read", "write"])
  res = await user_res
  if res.created_new_role:
    logger.info(f"Supertokens-UserRole: created {StRole.USER} role")
  res = await user_gold_res
  if res.created_new_role:
    logger.info(f"Supertokens-UserRole: created {StRole.USER_GOLD_TIER} role")
  res = await admin_res
  if res.created_new_role:
    logger.info(f"Supertokens-UserRole: created {StRole.ADMIN} role")


def verify_session_with_admin_role() -> Callable[..., Coroutine[Any, Any, "SessionContainer | None"]]:
  """Used for verify admin role in fastapi Depends style. We don't use this currently"""
  from supertokens_python.recipe.session.framework.fastapi import verify_session
  from supertokens_python.recipe.userroles import UserRoleClaim

  def new_validator(
    global_validators: list[SessionClaimValidator], session: "SessionContainer", user_context: dict[str, Any]
  ) -> list[SessionClaimValidator]:
    return global_validators + [UserRoleClaim.validators.includes(StRole.ADMIN.value)]

  return verify_session(
    # We add the UserRoleClaim's includes validator
    override_global_claim_validators=new_validator
  )


async def async_send_email(subject: str, body: str, is_html: bool, target_email: str) -> None:
  """Use this after Init-supertokens"""
  from supertokens_python.ingredients.emaildelivery.types import EmailContent
  from supertokens_python.recipe import emailpassword

  from .supertokens_config import _get_smtp_settings

  smtp_service = emailpassword.SMTPService(smtp_settings=_get_smtp_settings())
  content = EmailContent(
    subject=subject,
    body=body,
    to_email=target_email,
    is_html=is_html,
  )
  await smtp_service.service_implementation.transporter.send_email(content, {})


class CreatePasswordResetLinkRet(BaseModel):
  is_success: bool
  link: str | None
  fail_reason: str | None


async def async_create_password_reset_link(email: str) -> CreatePasswordResetLinkRet:
  """Return: (is-success, fail-reason)
  # the password reset link's lifetime is 1 hour.
  """
  users = await async_get_user_by_email(email)
  if not users:
    return CreatePasswordResetLinkRet(is_success=False, link=None, fail_reason=f"No user found for the email: {email}")

  u = users[0]  # always get the first one, ignore the other condition
  link = await create_reset_password_link("public", u.id, email)

  if isinstance(link, str):
    return CreatePasswordResetLinkRet(is_success=True, link=link, fail_reason=None)
  fail_reason = "user does not exist or is not an email password user"
  return CreatePasswordResetLinkRet(is_success=False, link=None, fail_reason=fail_reason)


async def async_manually_verify_email(email: str) -> tuple[bool, str | None]:
  users = await async_get_user_by_email(email)
  if not users:
    return (False, f"No user found for the email: {email}")

  u = users[0]  # always get the first one, ignore the other condition
  recipe_user_id = RecipeUserId(u.id)
  try:
    # Create an email verification token for the user
    token_res = await create_email_verification_token("public", recipe_user_id)

    # If the token creation is successful, use the token to verify the user's email
    if isinstance(token_res, CreateEmailVerificationTokenOkResult):
      await verify_email_using_token("public", token_res.token)
    return (True, None)
  except Exception as e:
    err = f"Failed to manually verify email, err={e}"
    logger.warning("%s", err)
    return (False, err)
