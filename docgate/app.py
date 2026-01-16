from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from supertokens_python import get_all_cors_headers
from supertokens_python.framework.fastapi import get_middleware
from fastapi import Depends

from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.session.framework.fastapi import verify_session


from docgate import config
from docgate.supertokens_config import init_supertokens

logger = config.LOGGER

logger.info("Init Supertokens")
init_supertokens()


app = FastAPI(
    title=f"{config.APP_NAME}-backend",
)

app.add_middleware(get_middleware())

# start apis

@app.post('/like_comment') 
async def like_comment(session: SessionContainer = Depends(verify_session())):
    user_id = session.get_user_id()

    print(user_id)
  

  
# after all the apis
app.add_middleware(
  CORSMiddleware,
  allow_origins=[config.WEBSITE_DOMAIN],
  allow_credentials=True,
  allow_methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"],
  allow_headers=["Content-Type"] + get_all_cors_headers(),
)
