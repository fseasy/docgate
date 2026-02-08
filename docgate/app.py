from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from supertokens_python import get_all_cors_headers
from supertokens_python.framework.fastapi import get_middleware

from docgate import config
from docgate.exceptions import ApiBaseException
from docgate.repositories import lifespan_db
from docgate.routes import admin_router, internal_auth_router, user_router
from docgate.supertokens_config import init_supertokens
from docgate.supertokens_utils import async_init_roles

logger = config.LOGGER

logger.info("Init Supertokens")
init_supertokens()


logger.info("Build app")


@asynccontextmanager
async def lifespan_main(app: FastAPI) -> AsyncGenerator[Any, None]:
  async with lifespan_db(app):
    await async_init_roles()
    yield


app = FastAPI(title=f"{config.APP_NAME}-backend", lifespan=lifespan_main)

app.add_middleware(get_middleware())

# start apis. NOTE: we've added the same prefix for all our self-hosted api! (for nginx routing!)
app.include_router(admin_router, prefix=config.API_COMMON_BASE_PATH)
app.include_router(internal_auth_router, prefix=config.API_COMMON_BASE_PATH)
app.include_router(user_router, prefix=config.API_COMMON_BASE_PATH)


@app.exception_handler(RequestValidationError)
async def input_param_validation_handler(exec: RequestValidationError):
  return JSONResponse(content={"error_type": "invalid-input-param", "error_detail": str(exec)}, status_code=400)


@app.exception_handler(ApiBaseException)
async def internal_exception_handler(exec: ApiBaseException):
  return JSONResponse(content={"error_type": "internal-error", "error_detail": str(exec)}, status_code=500)


@app.exception_handler(Exception)
async def unknown_internal_exception_handler(exec: Exception):
  return JSONResponse(content={"error_type": "unknown-internal-error", "error_detail": str(exec)}, status_code=500)


# after all the apis
app.add_middleware(
  CORSMiddleware,
  allow_origins=[config.WEBSITE_DOMAIN],
  allow_credentials=True,
  allow_methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"],
  allow_headers=["Content-Type"] + get_all_cors_headers(),
)
