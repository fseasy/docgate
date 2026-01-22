from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from supertokens_python import get_all_cors_headers
from supertokens_python.framework.fastapi import get_middleware

from docgate import config
from docgate.repositories import lifespan_db
from docgate.routes import admin_router, internal_auth_router, user_router
from docgate.supertokens_config import init_supertokens

logger = config.LOGGER

logger.info("Init Supertokens")
init_supertokens()


logger.info("Build app")
app = FastAPI(title=f"{config.APP_NAME}-backend", lifespan=lifespan_db)

app.add_middleware(get_middleware())

# start apis. NOTE: we've added the same prefix for all our self-hosted api! (for nginx routing!)
app.include_router(admin_router, prefix=config.API_COMMON_BASE_PATH)
app.include_router(internal_auth_router, prefix=config.API_COMMON_BASE_PATH)
app.include_router(user_router, prefix=config.API_COMMON_BASE_PATH)

# after all the apis
app.add_middleware(
  CORSMiddleware,
  allow_origins=[config.WEBSITE_DOMAIN],
  allow_credentials=True,
  allow_methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"],
  allow_headers=["Content-Type"] + get_all_cors_headers(),
)
