import argparse
import asyncio
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from docgate.models import Tier
from docgate.repositories import async_get_user, get_db_async_session_cxt, lifespan_db
from docgate.supertokens_config import StRole, init_supertokens
from docgate.supertokens_utils import async_add_role2user, async_get_user_by_email, async_init_roles


async def add_admin_for_emails(emails: Iterable[str], db_session: AsyncSession) -> None:
  init_supertokens()

  await async_init_roles()

  for email in emails:
    try:
      users = await async_get_user_by_email(email)
    except Exception as e:
      print(f"Error fetching user by email '{email}': {e}")
      continue

    if not users:
      print(f"No SuperTokens user found for email: {email}")
      continue

    for user in users:
      # SuperTokens user object has `id` attribute
      user_id = getattr(user, "id", None)
      if not user_id:
        print(f"User record for email {email} missing id: {user}")
        continue

      try:
        add_ok, add_tips = await async_add_role2user(user_id, StRole.ADMIN)
        if not add_ok:
          # add_role2user returns a string on error or when already had role
          print(f"Email={email} User={user_id}: add role failed, reason: {add_tips}")
        else:
          print(f"Email={email} User={user_id}: add role success, tips: {add_tips}")
        db_user = await async_get_user(db_session, user_id)
        if db_user is None:
          err = f"Email={email} User={user_id}: failed to get user from self-hosted db"
          print(err)
          raise Exception(err)
        db_user.tier = Tier.INTERNAL_MANAGER
        await db_session.commit()

      except Exception as e:
        print(f"Failed to add admin role for user {user_id} (email={email}): {e}")


async def main():
  parser = argparse.ArgumentParser(description="Add admin role to SuperTokens users by email")
  parser.add_argument("-e", "--email", nargs="+", required=True, help="Email(s) to add admin role for")
  args = parser.parse_args()

  async with lifespan_db(None), get_db_async_session_cxt() as session:
    await add_admin_for_emails(args.email, session)


if __name__ == "__main__":
  asyncio.run(main())
