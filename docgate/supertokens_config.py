import asyncio
import traceback
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
from supertokens_python.types.response import GeneralErrorResponse

from . import config as base_conf
from .logics import CreateUserStatus, FormFieldId, create_user_after_supertokens_signup, validate_password

logger = base_conf.LOGGER


def init_supertokens():
  supertokens_config = SupertokensConfig(
    connection_uri=base_conf.SUPERTOKENS_CONNECTION_URI, api_key=base_conf.SUPERTOKENS_API_KEY
  )

  app_info = InputAppInfo(
    app_name=base_conf.APP_NAME,
    api_domain=base_conf.API_DOMAIN,
    website_domain=base_conf.WEBSITE_DOMAIN,
    api_base_path=base_conf.API_BASE_PATH,
    website_base_path=base_conf.WEBSITE_BASE_PATH,
  )

  recipe_list = [session.init(), dashboard.init(), userroles.init(), _init_emailpassword()]

  logger.info("SuperTokens: Init supertokens")
  init(
    supertokens_config=supertokens_config,
    app_info=app_info,
    framework="fastapi",
    recipe_list=recipe_list,
    mode="asgi",
    telemetry=False,
  )
  logger.info("SuperTokens: Init done")


class StRole(StrEnum):
  USER = "user"
  ADMIN = "admin"


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
      loop = asyncio.get_running_loop()

      # Post sign up response, we check if it was successful
      if isinstance(response, SignUpPostOkResult):
        user = response.user
        status = await loop.run_in_executor(None, create_user_after_supertokens_signup, *(user, form_fields))
        if status == CreateUserStatus.INTERNAL_UNEXPECTED_ERROR:
          # need rollback on the supertokens side!
          from .supertokens_utils import async_delete_user

          try:
            await async_delete_user(user.id)
          except Exception as e:
            err_str = (
              f"Supertokens: delete user failed after create-user failure. user={user.to_json()}, "
              f"e=[{e}], stack={traceback.format_exc()}"
            )
            logger.error(f"{err_str}")
            response = GeneralErrorResponse(err_str)  # override response!
          else:
            response = GeneralErrorResponse(
              f"Failed due to internal create-user side error. user={user.to_json()}, Please contact admin"
            )  # override response!
        elif status == CreateUserStatus.CREATE_USER_FAILED_ON_SUPERTOKENS_INVALID_USER_DATA:
          response = GeneralErrorResponse(f"Failed due to supertokens invalid user data: {user.to_json()}")

      return response

    original_implementation.sign_up_post = sign_up_post
    return original_implementation

  async def _validate_password(value: str, _tenant_id: str) -> str | None:
    return validate_password(value)

  return emailpassword.init(
    override=emailpassword.InputOverrideConfig(apis=_override_email_password_apis),
    sign_up_feature=emailpassword.InputSignUpFeature(
      form_fields=[
        InputFormField(id="password", validate=_validate_password),
        InputFormField(id=FormFieldId.INVITE_CODE.value, optional=True),
        InputFormField(id="confirm-password"),
      ]
    ),
  )
