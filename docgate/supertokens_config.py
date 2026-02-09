import traceback
from enum import StrEnum
from typing import Any

from supertokens_python import InputAppInfo, SupertokensConfig, init
from supertokens_python.ingredients.emaildelivery.types import EmailDeliveryConfig, SMTPSettings, SMTPSettingsFrom
from supertokens_python.recipe import dashboard, emailpassword, emailverification, session, userroles
from supertokens_python.recipe.emailpassword.interfaces import (
  APIInterface,
  APIOptions,
  SignUpPostOkResult,
)
from supertokens_python.recipe.emailpassword.types import FormField
from supertokens_python.recipe.session.interfaces import (
  RecipeInterface as SessionRecipeInterface,
)
from supertokens_python.types import RecipeUserId
from supertokens_python.types.response import GeneralErrorResponse

from . import config as base_conf

logger = base_conf.LOGGER


def init_supertokens():
  supertokens_config = SupertokensConfig(
    connection_uri=base_conf.SUPERTOKENS_CONNECTION_URI, api_key=base_conf.SUPERTOKENS_API_KEY
  )

  app_info = InputAppInfo(
    app_name=base_conf.APP_NAME,
    api_domain=base_conf.API_DOMAIN,
    website_domain=base_conf.WEBSITE_DOMAIN,
    api_base_path=base_conf.API_AUTH_BASE_PATH,
    website_base_path=base_conf.WEBSITE_AUTH_BASE_PATH,
  )

  recipe_list = [
    emailverification.init(
      mode="REQUIRED",
      email_delivery=EmailDeliveryConfig(service=emailverification.SMTPService(smtp_settings=_get_smtp_settings())),
    ),
    session.init(
      expose_access_token_to_frontend_in_cookie_based_auth=True,
      override=session.InputOverrideConfig(functions=_override_session_functions),
    ),
    dashboard.init(),
    userroles.init(),
    _init_emailpassword(),
  ]

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
  USER_GOLD_TIER = "user_gold_tier"
  ADMIN = "admin"


def _init_emailpassword():
  from supertokens_python.recipe.emailpassword import InputFormField

  from .logics import CreateDbUserLogic, CreateUserStatus, FormFieldId, UserPermissionLogic, validate_password

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
        user = response.user
        db_create_status = await CreateDbUserLogic.async_create_after_supertokens_signup(user, form_fields)
        if db_create_status == CreateUserStatus.CREATE_AND_REDEEM_SUCCESS:
          # code is valid. set read role
          try:
            await UserPermissionLogic.async_set_doc_reading_permission(response.session, user_id=user.id)
          except Exception as e:
            err_str = f"SetDocReadingPermission: failed to set permission due to error: {e}"
            logger.warning("%s", err_str)
            response = GeneralErrorResponse(f"设置文档权限失败, 请联系{base_conf.CONTENT_AUTHOR_NAME}.")  #
        elif db_create_status == CreateUserStatus.INTERNAL_UNEXPECTED_ERROR:
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
        elif db_create_status == CreateUserStatus.CREATE_USER_FAILED_ON_SUPERTOKENS_INVALID_USER_DATA:
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
        InputFormField(id=FormFieldId.PREPAID_CODE.value, optional=True),
        InputFormField(id="confirm-password"),
      ]
    ),
    email_delivery=EmailDeliveryConfig(service=emailpassword.SMTPService(smtp_settings=_get_smtp_settings())),
  )


def _get_smtp_settings() -> SMTPSettings:
  from email.header import Header

  c = base_conf.SMTP_CONF

  encoded_name = Header(c.account_name, "utf-8").encode()

  return SMTPSettings(
    host=c.host,
    port=c.port,
    from_=SMTPSettingsFrom(name=encoded_name, email=c.account_email),
    password=c.account_password,
    secure=c.secure,
    username=c.account_email,  # this is optional. In case not given, from_.email will be used
  )


def _override_session_functions(original_implementation: SessionRecipeInterface):
  from .supertokens_utils import async_get_user

  original_create_new_session = original_implementation.create_new_session

  async def create_new_session(
    user_id: str,
    recipe_user_id: RecipeUserId,
    access_token_payload: dict[str, Any] | None,
    session_data_in_database: dict[str, Any] | None,
    disable_anti_csrf: bool | None,
    tenant_id: str,
    user_context: dict[str, Any],
  ):
    # * Add email to the access session payload
    user_data = await async_get_user(user_id)
    if user_data and user_data.emails:
      email = user_data.emails[0]
      access_token_payload = access_token_payload or {}
      access_token_payload["email"] = email

    return await original_create_new_session(
      user_id,
      recipe_user_id,
      access_token_payload,
      session_data_in_database,
      disable_anti_csrf,
      tenant_id,
      user_context,
    )

  original_implementation.create_new_session = create_new_session
  return original_implementation
