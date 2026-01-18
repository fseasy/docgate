from supertokens_python.recipe.userroles.interfaces import UnknownRoleError
from supertokens_python.recipe.userroles.syncio import add_role_to_user, create_new_role_or_add_permissions
from supertokens_python.types import User

from . import config as base_conf
from .supertokens_config import StRole

logger = base_conf.LOGGER


def get_user_by_email(email: str) -> list[User]:
  from supertokens_python.syncio import list_users_by_account_info
  from supertokens_python.types.base import AccountInfoInput

  user_infos = list_users_by_account_info("public", AccountInfoInput(email=email))
  return user_infos


def add_role2user(user_id: str, role: StRole) -> str | None:
  """Return None if all success, else return error/warning info"""
  res = add_role_to_user("public", user_id, role)
  if isinstance(res, UnknownRoleError):
    return f"Unknown role, err={res}"
  if res.did_user_already_have_role:
    return f"User {user_id} already has role of {role}"


def create_role():
  """NOTE: can't put this function in the app-run process, or it will exit with following exception:
  ```bash
    return loop.run_until_complete(co)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "uvloop/loop.pyx", line 1512, in uvloop.loop.Loop.run_until_complete
    File "uvloop/loop.pyx", line 1505, in uvloop.loop.Loop.run_until_complete
    File "uvloop/loop.pyx", line 1379, in uvloop.loop.Loop.run_forever
    File "uvloop/loop.pyx", line 520, in uvloop.loop.Loop._run
  RuntimeError: this event loop is already running.
  ```
  NOTE: you can only create role on yourself environment. i.e., you can't create role in the `try.supertokens.io`
  """
  res = create_new_role_or_add_permissions(StRole.USER, ["read"])
  if res.created_new_role:
    logger.info(f"Supertokens-UserRole: created {StRole.USER} role")
  res = create_new_role_or_add_permissions(StRole.ADMIN, ["read", "write"])
  if res.created_new_role:
    logger.info(f"Supertokens-UserRole: created {StRole.ADMIN} role")


def verify_session_with_admin_role():
  from supertokens_python.recipe.session.framework.fastapi import verify_session
  from supertokens_python.recipe.userroles import UserRoleClaim

  def new_validator(global_validators, session, user_context):
    return global_validators + [UserRoleClaim.validators.includes(StRole.ADMIN.value)]

  return verify_session(
    # We add the UserRoleClaim's includes validator
    override_global_claim_validators=new_validator
  )
