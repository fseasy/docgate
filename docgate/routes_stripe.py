import traceback
from datetime import datetime
from typing import Annotated, Any

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.session.asyncio import get_session, refresh_session
from supertokens_python.recipe.session.framework.fastapi import verify_session
from supertokens_python.recipe.userroles import UserRoleClaim

from docgate import config
from docgate.asserts import gen_purchase_confirmation_email_html_body
from docgate.exceptions import InvalidUserInputException, LogicError
from docgate.logics import PaywallLogic, UserPermissionLogic
from docgate.models import PayLog, Tier
from docgate.repositories import (
  async_get_user,
  get_db_async_session,
  get_db_async_session_cxt,
)
from docgate.supertokens_config import StRole
from docgate.supertokens_utils import async_send_email

stripe_router = APIRouter(prefix="/stripe", tags=["UserStripe"])

logger = config.LOGGER


@stripe_router.post("/create-checkout-session")
async def create_checkout_session(
  st_session: SessionContainer = Depends(verify_session()),
):
  def _build_return_url():
    url = config.get_website_full_url(config.STRIPE_RETURN_ROUTE_PATH)
    return url + "?session_id={CHECKOUT_SESSION_ID}"  # CHECKOUT_SESSION_ID is template var for stripe

  payload = st_session.get_access_token_payload()
  email = payload.get("email", None)
  if email:  # can't use empty-string, or error; can't directly pass None to function, ruff complains
    kwargs = {"customer_email": email}
  else:
    kwargs = {}

  return_url = _build_return_url()

  stripe_session = await stripe.checkout.Session.create_async(
    ui_mode="custom",
    **kwargs,
    billing_address_collection="auto",
    line_items=[
      {
        "price": config.STRIP_PRICE_ID,
        "quantity": 1,
      },
    ],
    metadata={"user_id": st_session.get_user_id()},
    mode="payment",
    return_url=return_url,
  )
  return {"clientSecret": stripe_session.client_secret}


@stripe_router.get("/session-status")
async def session_status(session_id: str):
  session = await stripe.checkout.Session.retrieve_async(session_id)
  return {
    "status": session.status,
    "customer_email": session.customer_details.email if session.customer_details else None,
  }


@stripe_router.post("/fulfill-checkout-webhook")
async def fulfill_checkout_webhook(request: Request, stripe_signature: str = Header(None)):
  # 1. 获取原始字节流 (Raw Body)
  payload = await request.body()
  if not stripe_signature:
    print("HEADER wrong")
    raise HTTPException(status_code=400, detail="Missing stripe-signature header")

  event = None

  try:
    # 2. 验证签名
    # 注意：construct_event 是同步方法，但在 FastAPI 中直接运行很快，通常不需要专门封装
    event = stripe.Webhook.construct_event(payload, stripe_signature, config.STRIP_ENDPOINT_SECRET)
  except ValueError as e:
    print("payload wrong", e)
    raise HTTPException(status_code=400, detail=f"Invalid payload, {e}")
  except stripe.SignatureVerificationError as e:
    print("signature wrong", e)
    raise HTTPException(status_code=400, detail=f"Invalid signature, {e}")

  event_type = event["type"]

  if event_type == "checkout.session.completed" or event_type == "checkout.session.async_payment_succeeded":
    print("check")
    session = event["data"]["object"]
    await fulfill_checkout(session["id"])

  return Response(content="Success", status_code=200)


async def fulfill_checkout(session_id: str):
  print("Fulfilling Checkout Session", session_id)

  # TODO: Make this function safe to run multiple times,
  # even concurrently, with the same session ID
  # TODO: Make sure fulfillment hasn't already been
  # performed for this Checkout Session

  # Retrieve the Checkout Session from the API with line_items expanded
  checkout_session = await stripe.checkout.Session.retrieve_async(
    session_id,
    expand=["line_items"],
  )
  is_paid_success = checkout_session.payment_status != "unpaid"
  # sync status to db
  metadata = checkout_session.metadata
  if not metadata:
    logger.error("Stripe: Fulfill checkout, can't get metadata from checkout session")
    return
  user_id = metadata.get("user_id", None)
  if user_id is None:
    raise LogicError(
      f"Stripe: Fulfill checkout, can't get user_id from metadata({metadata})",
    )
  customer_detail = checkout_session.customer_details
  if customer_detail is None:
    raise LogicError("Stripe: got customer detail as None. impossible")
  email = customer_detail.email
  if email is None:
    raise LogicError("Stripe: got customer details.email as None. Impossible")
  async with get_db_async_session_cxt() as db_session:
    if is_paid_success:
      await PaywallLogic.set_db_user_paid(db_session=db_session, user_id=user_id, email=email)
      # ! here we can't retrieval user session. so user-permission can't be update here.
      # ! we'll do it in the return part.
      logger.info(
        f"Stripe: set user paid success: user=[{user_id}, {email}]. "
        "NOTE: user permission haven't been synced to supertokens session"
      )
    else:
      await PaywallLogic.set_db_user_pay_failed(db_session=db_session, user_id=user_id, email=email)


class AfterPayReq(BaseModel):
  target_email: Annotated[
    str, Field(description="used to send email"), StringConstraints(strip_whitespace=True, min_length=1)
  ]


class AfterPayResp(BaseModel):
  fail_reason: str | None


@stripe_router.post("/after-pay")
async def after_pay(
  req: AfterPayReq,
  st_session: SessionContainer = Depends(verify_session()),
  db_session: AsyncSession = Depends(get_db_async_session),
):
  """
  1. check if it success. (should only be triggered after successfully pay. but may have dirty input.)
  2. add doc-reading permission (it can only be done here, with supertokens session)
  3. send email.
  """
  user_id = st_session.user_id
  db_user = await async_get_user(db_session, user_id=user_id, for_update=False)
  if not db_user:
    return AfterPayResp(fail_reason=f"User {user_id}(tgt-email=[{req.target_email}]) doesn't exist in db")
  if db_user.tier == Tier.FREE:
    logger.warning(f"AfterPay: get a free user: id=[{user_id}], tgt-email=[{req.target_email}]")
    return AfterPayResp(fail_reason=f"User {user_id}(tgt-email=[{req.target_email}]) hadn't paid")
  # check done.
  # - set permission
  await UserPermissionLogic.async_set_doc_reading_permission(st_session=st_session, user_id=user_id)
  body = gen_purchase_confirmation_email_html_body(req.target_email)
  await async_send_email(
    subject=f"感谢购买「{config.APP_LOCALE_NAME}」", body=body, is_html=True, target_email=req.target_email
  )
  return AfterPayResp(fail_reason=None)
