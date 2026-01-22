import asyncio

from docgate.models import async_engine
from docgate.repositories import async_get_user, get_db_async_session_cxt

uid = "52b477e1-a881-460e-a79b-3c9df16eac63"


async def main():
  async with get_db_async_session_cxt() as session:
    u = await async_get_user(session, uid)
  print(u)
  print("END")
  await async_engine.dispose()


asyncio.run(main())
