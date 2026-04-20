from fastapi import Depends, Header, HTTPException
from fastapi_jwt import JwtAuthorizationCredentials

from app.core.subscription import (
  ensure_active_subscription_or_raise,
  get_internal_job_token,
)
from jwt_auth import verify_jwt


async def require_active_subscription(
  user: JwtAuthorizationCredentials = Depends(verify_jwt),
) -> JwtAuthorizationCredentials:
  await ensure_active_subscription_or_raise()
  return user


async def require_active_admin_subscription(
  user: JwtAuthorizationCredentials = Depends(verify_jwt),
) -> JwtAuthorizationCredentials:
  await ensure_active_subscription_or_raise()
  return user


async def verify_internal_job_token(
  x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> None:
  expected_token = get_internal_job_token()
  if not expected_token:
    raise HTTPException(
      status_code=503,
      detail="INTERNAL_JOB_TOKEN belum dikonfigurasi.",
    )

  if x_internal_token != expected_token:
    raise HTTPException(status_code=401, detail="Internal token tidak valid.")
