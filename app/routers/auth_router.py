from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.responses import JSONResponse
from fastapi_jwt import JwtAuthorizationCredentials

from app.controllers.auth_controller import (
  confirm_bind,
  get_current_user,
  login_user,
  refresh_user_token,
)
from app.dependencies import require_active_subscription
from app.schemas.requests.auth import LoginRequest
from jwt_auth import refresh_security

router = APIRouter(tags=["Auth"])


@router.post("/login")
async def login(payload: LoginRequest):
  try:
    return await login_user(payload)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail},
      status_code=e.status_code,
    )
  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": f"Koneksi Error {str(e)}"},
      status_code=500,
    )


@router.get("/user")
async def user(
  is_admin: bool = False,
  auth_user: JwtAuthorizationCredentials = Depends(require_active_subscription),
):
  try:
    return await get_current_user(auth_user=auth_user, is_admin=is_admin)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail},
      status_code=e.status_code,
    )
  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": f"Koneksi Error {str(e)}"},
      status_code=500,
    )


@router.put("/confirm-bind")
async def confirm_bind_route(
  auth_user: JwtAuthorizationCredentials = Depends(require_active_subscription),
):
  try:
    return await confirm_bind(auth_user)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail},
      status_code=e.status_code,
    )
  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": f"Koneksi Error {str(e)}"},
      status_code=500,
    )


@router.post("/refresh-token")
async def refresh_token(
  auth_user: JwtAuthorizationCredentials = Security(refresh_security),
):
  try:
    return await refresh_user_token(auth_user)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail},
      status_code=e.status_code,
    )
  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": f"Koneksi Error {str(e)}"},
      status_code=500,
    )
