import argparse
import asyncio
from typing import Iterable

from docgate.supertokens_config import StRole, init_supertokens
from docgate.supertokens_utils import async_add_role2user, async_get_user_by_email


async def add_admin_for_emails(emails: Iterable[str]) -> None:
  init_supertokens()

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
        result_info = await async_add_role2user(user_id, StRole.ADMIN)
        if result_info:
          # add_role2user returns a string on error or when already had role
          print(f"Email={email} User={user_id}: add role get warning/error: {result_info}")
        else:
          print(f"Email={email} User={user_id}: add role success")
      except Exception as e:
        print(f"Failed to add admin role for user {user_id} (email={email}): {e}")


def main():
  parser = argparse.ArgumentParser(description="Add admin role to SuperTokens users by email")
  parser.add_argument("-e", "--email", nargs="+", required=True, help="Email(s) to add admin role for")
  args = parser.parse_args()

  asyncio.run(add_admin_for_emails(args.email))


if __name__ == "__main__":
  main()
