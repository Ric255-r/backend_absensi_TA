from fastapi import APIRouter, HTTPException, Request, Security
from fastapi.responses import JSONResponse
from fastapi_jwt import JwtAuthorizationCredentials

from app.controllers.user_controller import update_password, update_profile
from app.schemas.requests.auth import PasswordUpdateRequest
from jwt_auth import access_security

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/update_profile")
async def update_profile_route(
  request: Request,
  user: JwtAuthorizationCredentials = Security(access_security),
):
  try:
    form = await request.form()
    return await update_profile(dict(form), user)
  except HTTPException as e:
    return JSONResponse(content={"status": "error", "message": e.detail}, status_code=e.status_code)
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/update_password")
async def update_password_route(
  payload: PasswordUpdateRequest,
  user: JwtAuthorizationCredentials = Security(access_security),
):
  try:
    return await update_password(payload, user)
  except HTTPException as e:
    return JSONResponse(content={"status": "error", "message": e.detail}, status_code=e.status_code)
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

