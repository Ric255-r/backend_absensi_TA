import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi_jwt import JwtAuthorizationCredentials

from app.controllers.user_controller import FOTO_PROFILE, update_password, update_profile
from app.dependencies import require_active_subscription
from app.schemas.requests.auth import PasswordUpdateRequest

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/foto_profile/{filename}")
def get_foto_profile(filename: str):
  safe_filename = os.path.basename(filename)
  if safe_filename != filename:
    raise HTTPException(status_code=400, detail="Nama file tidak valid")

  img_path = os.path.join(FOTO_PROFILE, safe_filename)
  if not os.path.isfile(img_path):
    raise HTTPException(status_code=404, detail="File foto profile tidak ditemukan")

  return FileResponse(img_path, media_type="image/png")

@router.post("/update_profile")
async def update_profile_route(
  request: Request,
  user: JwtAuthorizationCredentials = Depends(require_active_subscription),
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
  user: JwtAuthorizationCredentials = Depends(require_active_subscription),
):
  try:
    return await update_password(payload, user)
  except HTTPException as e:
    return JSONResponse(content={"status": "error", "message": e.detail}, status_code=e.status_code)
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
