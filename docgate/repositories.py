from datetime import datetime

from .models import InviteCode, User, db, PayMethod, Tier
from peewee import ErrorSavingData


def get_user(user_id: str) -> User | None:
  return User.get_or_none(User.id == user_id)


def record_invite_code(code: str, lifetime: datetime) -> InviteCode:
  new_code = InviteCode(code=code, lifetime=lifetime, has_used=False)
  new_code.save()
  return new_code


def get_invite_code(code: str) -> InviteCode | None:
  return InviteCode.get_or_none(code == code)


def add_user_with_redeeming_invite_code(user_id: str, email: str, invite_code: InviteCode) -> str | None:
  """No exceptions. return an error str on failure, or None on success"""
  with db.atomic() as transaction:
    try:
      user = User(external_id=user_id, email=email, pay_method=str(PayMethod.INVITE_CODE), lifetime=None, tier=int(Tier.GOLD))
      invite_code.has_used = True
      user.save()
      invite_code.save()
    except ErrorSa
    