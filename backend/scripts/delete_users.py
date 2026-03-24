import argparse
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from docgate.config import LOGGER as logger
from docgate.repositories import async_delete_user, get_db_async_session_cxt, lifespan_db
from docgate.supertokens_config import init_supertokens
from docgate.supertokens_utils import async_delete_user as supertokens_async_delete_user, async_get_user_by_email


async def get_user_id2email_from_emails(emails: list[str]) -> dict[str, str]:
  uid2email: dict[str, str] = {}
  for email in emails:
    try:
      users = await async_get_user_by_email(email)
    except Exception as e:
      print(f"Error fetching user by email '{email}': {e}")
      continue
    if not users:
      print(f"No SuperTokens user found for email: {email}")
      continue
    uid2email.update([(u.id, email) for u in users])
  print(f"Total get {len(uid2email)} user-ids from {len(emails)} emails")
  return uid2email


async def delete_user_by_ids(user_ids: set[str], db_session: AsyncSession, uid2email: dict[str, str]) -> None:
  """uid2email may only contain partial uid data!"""
  print(f"Ready to delete {len(user_ids)} users")
  for user_id in user_ids:
    print(f"DELETE USER_ID: {user_id}, email={uid2email.get(user_id)}", end=", ")
    try:
      db_task = async_delete_user(db_session, user_id)
      supertokens_delete_task = supertokens_async_delete_user(user_id)
      await supertokens_delete_task
      db_delete_err = await db_task
      await db_session.commit()
      if db_delete_err:
        print(f"Delete User in DB failed with: {db_delete_err}. [Error is acceptable and is ignored]", end=", ")
      print("[SUCCESS]")
    except Exception as e:
      logger.exception("Delete Get exception")
      print(f"Failed to delete user for user {user_id}, err={e}. FAILED for this item. [FAILED]")


async def main():
  parser = argparse.ArgumentParser(description="Delete User (Supertokens & db) by email/user-id")
  parser.add_argument("-e", "--email", nargs="+", help="Email(s) to be deleted")
  parser.add_argument("-u", "--user_id", nargs="+", help="User(s) be deleted")
  args = parser.parse_args()

  if not args.email and not args.user_id:
    raise Exception("At least 1 user/email")

  async with lifespan_db(None), get_db_async_session_cxt() as session:
    init_supertokens()

    uid_to_email = await get_user_id2email_from_emails(args.email)
    all_uids = set(uid_to_email.keys()) | set(args.user_id or [])
    await delete_user_by_ids(all_uids, session, uid_to_email)


if __name__ == "__main__":
  asyncio.run(main())
