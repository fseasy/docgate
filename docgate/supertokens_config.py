from enum import StrEnum
from typing import Any

from supertokens_python import InputAppInfo, SupertokensConfig, init
from supertokens_python.recipe import dashboard, emailpassword, session, userroles
from supertokens_python.recipe.emailpassword.interfaces import (
  APIInterface,
  APIOptions,
  SignUpPostOkResult,
)
from supertokens_python.recipe.emailpassword.types import FormField
from supertokens_python.types import User as StUser

from . import config as base_conf
from .logics import InviteCode as InviteCodeLogic
from .repositories import get_invite_code

logger = base_conf.LOGGER


def init_supertokens():
  def get_api_domain() -> str:
    return base_conf.API_DOMAIN

  def get_website_domain() -> str:
    return base_conf.WEBSITE_DOMAIN

  supertokens_config = SupertokensConfig(connection_uri="https://try.supertokens.com")

  app_info = InputAppInfo(
    app_name=base_conf.APP_NAME,
    api_domain=get_api_domain(),
    website_domain=get_website_domain(),
    api_base_path="/auth",
    website_base_path="/auth",
  )

  recipe_list = [session.init(), dashboard.init(), userroles.init(), _init_emailpassword()]

  init(
    supertokens_config=supertokens_config,
    app_info=app_info,
    framework="fastapi",
    recipe_list=recipe_list,
    mode="asgi",
    telemetry=False,
  )


class FormFieldId(StrEnum):
  INVITE_CODE = "invite-code"


def _init_emailpassword():
  from supertokens_python.recipe.emailpassword import InputFormField

  def _override_email_password_apis(original_implementation: APIInterface):
    from supertokens_python.recipe.session.interfaces import SessionContainer

    original_sign_up_post = original_implementation.sign_up_post

    async def sign_up_post(
      form_fields: list[FormField],
      tenant_id: str,
      session: SessionContainer | None,
      should_try_linking_with_session_user: bool | None,
      api_options: APIOptions,
      user_context: dict[str, Any],
    ):
      # First we call the original implementation of sign_up_post.
      response = await original_sign_up_post(
        form_fields,
        tenant_id,
        session,
        should_try_linking_with_session_user,
        api_options,
        user_context,
      )

      # Post sign up response, we check if it was successful
      if isinstance(response, SignUpPostOkResult):
        _post_signup(response.user, form_fields)

      return response

    original_implementation.sign_up_post = sign_up_post
    return original_implementation

  async def _validate_password(value: str, _tenant_id: str):
    import re

    print("password = ", value)

    if re.search(r"[s]", value):
      return "Password can't contain whitespace"

  return emailpassword.init(
    sign_up_feature=emailpassword.InputSignUpFeature(
      form_fields=[
        InputFormField(id="password", validate=_validate_password),
        InputFormField(id="invite-code", optional=True),
        InputFormField(id="confirm-password"),
      ]
    )
  )


def _post_signup(user: StUser, form_fields: list[FormField]):
  def _create_free_user():
    

  invite_code_field: FormField | None = None
  for f in form_fields:
    if f.id == FormFieldId.INVITE_CODE:
      invite_code_field = f
      break
  if invite_code_field is None:
    logger.warning("Invite-code: no form field found!")
    return
  invite_code = invite_code_field.value
  code_data = get_invite_code(invite_code)
  if not code_data:
    logger.warning(f"Invite-code: can't find code={invite_code} in db")
    return
  is_redeemable, err = code_data.is_redeemable()
  if not is_redeemable:
    logger.warning(f"Invite-code: can't redeem code={invite_code}, err={err}")
    return
