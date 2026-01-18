from typing import TYPE_CHECKING, Generator

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from supertokens_python import get_all_cors_headers
from supertokens_python.framework.fastapi import get_middleware
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.session.framework.fastapi import verify_session

from docgate import config
from docgate.logics import InviteCode
from docgate.models import Tier
from docgate.repositories import create_invite_code, get_db_session, get_user
from docgate.supertokens_config import init_supertokens

if TYPE_CHECKING:
  from sqlalchemy.orm import Session


logger = config.LOGGER

logger.info("Init Supertokens")
init_supertokens()


logger.info("Build app")
app = FastAPI(
  title=f"{config.APP_NAME}-backend",
)

app.add_middleware(get_middleware())

# start apis


class InviteResult(BaseModel):
  error: str | None
  code: str | None
  lifetime: str | None


@app.post("/gen_invite_code")
async def gen_invite(
  session: SessionContainer = Depends(verify_session()), db_session: Session = Depends(get_db_session)
) -> InviteResult:
  """generate invite-code, record it to table"""

  def _logic():
    user_id = session.get_user_id()
    user = get_user(db_session, user_id)
    # assert user has the permission
    if not user or user.tier != Tier.INTERNAL_MANAGER:
      return InviteResult(
        error=f"user: {user_id} doesn't have permission to generate invite code", code=None, lifetime=None
      )
    invite_code = InviteCode.gen_invite_code()
    lifetime = InviteCode.get_lifetime()
    create_invite_code(db_session, invite_code, lifetime)
    return InviteResult(error=None, code=invite_code, lifetime=lifetime.strftime("%Y-%m-%d %H:%M:%S %z"))

  try:
    return _logic()
  except Exception as e:
    return InviteResult(error=str(e), code=None, lifetime=None)


# after all the apis
app.add_middleware(
  CORSMiddleware,
  allow_origins=[config.WEBSITE_DOMAIN],
  allow_credentials=True,
  allow_methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"],
  allow_headers=["Content-Type"] + get_all_cors_headers(),
)
