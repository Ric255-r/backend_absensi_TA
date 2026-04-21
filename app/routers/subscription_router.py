from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi_jwt import JwtAuthorizationCredentials

from app.controllers import subscription_controller
from app.core.audit import enable_audit, set_audit_actor
from app.schemas.requests.admin import (
  SubscriptionCreateRequest,
  SubscriptionExpireRequest,
  SubscriptionExtendRequest,
)
from jwt_auth import verify_jwt

router = APIRouter(tags=["Subscription"])


def _subject(user: JwtAuthorizationCredentials | dict) -> dict:
  return user.subject if hasattr(user, "subject") else user


async def verify_subscription_admin(
  user: JwtAuthorizationCredentials = Depends(verify_jwt),
) -> JwtAuthorizationCredentials:
  payload = _subject(user)
  if payload.get("roles") not in {"admin", "owner"}:
    raise HTTPException(status_code=403, detail="Akses subscription dibatasi")

  enable_audit(True)
  set_audit_actor(user)
  return user


@router.get("/subscription/status")
async def get_subscription_status():
  try:
    return await subscription_controller.get_subscription_status()
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail},
      status_code=e.status_code,
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/admin/subscriptions")
async def list_subscriptions(
  limit: int = Query(25, ge=1, le=100),
  user: JwtAuthorizationCredentials = Depends(verify_subscription_admin),
):
  try:
    return await subscription_controller.list_subscriptions(limit=limit)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail},
      status_code=e.status_code,
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.post("/admin/subscriptions")
async def create_subscription(
  payload: SubscriptionCreateRequest,
  user: JwtAuthorizationCredentials = Depends(verify_subscription_admin),
):
  try:
    return await subscription_controller.create_subscription(payload, actor=user)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail},
      status_code=e.status_code,
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/admin/subscriptions/{id_subscription}/history")
async def get_subscription_history(
  id_subscription: int,
  user: JwtAuthorizationCredentials = Depends(verify_subscription_admin),
):
  try:
    return await subscription_controller.get_subscription_history(
      id_subscription=id_subscription
    )
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail},
      status_code=e.status_code,
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/admin/subscriptions/{id_subscription}/extend")
async def extend_subscription(
  id_subscription: int,
  payload: SubscriptionExtendRequest,
  user: JwtAuthorizationCredentials = Depends(verify_subscription_admin),
):
  try:
    return await subscription_controller.extend_subscription(
      id_subscription=id_subscription,
      payload=payload,
      actor=user,
    )
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail},
      status_code=e.status_code,
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/admin/subscriptions/{id_subscription}/expire")
async def expire_subscription(
  id_subscription: int,
  payload: SubscriptionExpireRequest,
  user: JwtAuthorizationCredentials = Depends(verify_subscription_admin),
):
  try:
    return await subscription_controller.expire_subscription(
      id_subscription=id_subscription,
      payload=payload,
      actor=user,
    )
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail},
      status_code=e.status_code,
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
