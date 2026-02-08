from supertokens_python.recipe.userroles.asyncio import add_role_to_user, create_new_role_or_add_permissions
from supertokens_python.recipe.userroles.interfaces import UnknownRoleError
from supertokens_python.types import User

from . import config as base_conf
from .supertokens_config import StRole

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

  user_infos = await list_users_by_account_info("public", AccountInfoInput(email=email))
  return user_infos


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


async def async_init_roles():
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


def verify_session_with_admin_role():
  """Used for verify admin role in fastapi Depends style. We don't use this currently"""
  from supertokens_python.recipe.session.framework.fastapi import verify_session
  from supertokens_python.recipe.userroles import UserRoleClaim

  def new_validator(global_validators, session, user_context):
    return global_validators + [UserRoleClaim.validators.includes(StRole.ADMIN.value)]

  return verify_session(
    # We add the UserRoleClaim's includes validator
    override_global_claim_validators=new_validator
  )
