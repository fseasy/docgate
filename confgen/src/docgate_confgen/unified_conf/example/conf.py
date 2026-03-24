# after `uv sync`, it'll install the package as docgate_confgen
from docgate_confgen.data_types import (
  BasicConfigT,
  DeployConfT,
  EnvConfT,
  NginxConfT,
  NginxLogConf,
  SMTPConfT,
  StripeConfT,
  SupabaseConfT,
  SupertokensConfT,
  SyslogReceiverAddress,
)

_basic = BasicConfigT(
  # Please change all the naming based on your app
  VITE_APP_NAME="DajuanEnglish",
  # used in locale show env",
  VITE_APP_LOCALE_NAME="大娟的亲子英语",
  VITE_CONTENT_AUTHOR_NAME="大娟",
  # site set",
  VITE_API_DOMAIN="http://localhost:3333",
  VITE_API_COMMON_BASE_PATH="/api",
  VITE_API_AUTH_BASE_PATH="/api/auth",  # NOTE: it follows the `common-base-path`",
  # use this common base path to make the Nginx route react/hugo part more easily.",
  VITE_WEBSITE_DOMAIN="http://localhost:3333",
  VITE_WEBSITE_REACT_BASE_PATH="/app",
  VITE_WEBSITE_AUTH_BASE_PATH="/app/auth",  # it's within the react part, so it contains the /app prefix",
  VITE_WEBSITE_DOC_ROOT_PATH="/docs/",  # NOTE: keep the last `/` as it is better for Nginx and static site.",
  VITE_WEBSITE_INDEX_ROOT_PATH="/",
)

_supertokens = SupertokensConfT(
  SUPERTOKENS_CONNECTION_URI="https://st-dev-xxxxx",
  SUPERTOKENS_API_KEY="cdefapikey",
)

_strip = StripeConfT(
  VITE_STRIPE_RETURN_ROUTE_PATH="/app/stripe-return",  # within the react part. we put the prefix into it as auth.",
  VITE_STRIPE_PUBLISHABLE_API_KEY="pk_test_TEST_STRIP_PUBLISHABLE_KEY",
  STRIPE_API_KEY="sk_test_TEST_STRIP_API_KEY",
  ## This is the local webhook test key (use with `./docgate/scripts/stripe_listen.sh`)
  STRIPE_ENDPOINT_SECRET="whsec_local_end_point",
  STRIPE_PRICE_ID="price_id_NOTE_ITS_PRICE_ID_NOT_ITEM_ID",
)

_supabase = SupabaseConfT(
  SUPABASE_USER="supabase-user",
  SUPABASE_PASSWD="supabase-pass-thank-you",
  SUPABASE_HOST="aws-1-us-west-1.pooler.supabase.com",
  SUPABASE_PORT=5432,
  SUPABASE_DBNAME="postgres",
)


_syslog_addr = SyslogReceiverAddress()
_syslog_nginx_setting_prefix = f"syslog:server={_syslog_addr.host}:{_syslog_addr.port}"


_deploy = DeployConfT(
  vite_in_server_mode=True,
  # it's not necessary to keep the last slash
  # adjust them based on your server location
  vite_static_dir="/Users/fseasy/workspace/dev-repo/docgate/frontend/dist/",
  hugo_static_dir="/Users/fseasy/workspace/dev-repo/dajuan-english/dist/",
  nginx=NginxConfT(
    standard_reverse_proxy=False,
    access_log=NginxLogConf(type="syslog", setting=f"{_syslog_nginx_setting_prefix},tag=site_docgate,severity=info"),
    error_log=NginxLogConf(
      type="syslog", setting=f"{_syslog_nginx_setting_prefix},tag=site_docgate_err,severity=error"
    ),
  ),
  syslog_receiver_address=_syslog_addr,
)

_smtp = SMTPConfT(
  SMTP_HOST="smtp.xxx@xx.com",
  SMTP_PORT=465,
  SMTP_ACCOUNT_EMAIL="email_account@xx.com",
  SMTP_ACCOUNT_PASSWD="email_login_or_app_passwd",
  # SMTP_SECURE = true/false (based on the account setting),
  SMTP_SECURE=True,
)

Conf = EnvConfT(basic=_basic, supabase=_supabase, supertokens=_supertokens, smtp=_smtp, stripe=_strip, deploy=_deploy)
