from pathlib import Path

from ..config import APP_LOCALE_NAME

_dir = Path(__file__).parent.absolute()

with open(_dir / "purchase_confirmation.html", encoding="utf-8") as f:
  _purchase_confirmation_content = f.read().replace("{APP_NAME}", APP_LOCALE_NAME)


def gen_purchase_confirmation_email_html_body(user_name: str) -> str:
  return _purchase_confirmation_content.replace("{USER_NAME}", user_name)
