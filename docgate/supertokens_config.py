from supertokens_python.recipe import session
from supertokens_python.recipe import dashboard
from supertokens_python.recipe import userroles
from supertokens_python.recipe import emailpassword
from supertokens_python import init, InputAppInfo, SupertokensConfig

import docgate.config as base_conf


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

  recipe_list = [session.init(), dashboard.init(), userroles.init(), emailpassword.init()]

  init(
    supertokens_config=supertokens_config,
    app_info=app_info,
    framework="fastapi",
    recipe_list=recipe_list,
    mode="asgi",
    telemetry=False,
  )
