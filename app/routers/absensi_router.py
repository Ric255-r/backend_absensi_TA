import os
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Security
from fastapi.responses import FileResponse, JSONResponse
from fastapi_jwt import JwtAuthorizationCredentials
from pydantic import ValidationError
from starlette.datastructures import UploadFile

from app.controllers.absensi_controller import get_attendance_data, validate_check_in_attendance, validate_check_out_attendance, store_check_in_attendance, store_check_out_attendance
from app.schemas.requests.absensi import CheckInRequest, CheckOutRequest
from jwt_auth import access_security

router = APIRouter(prefix="/absen", tags=["Absensi"])

LATITUDE_BENGKOM = -0.0544064
LONGITUDE_BENGKOM = 109.3732664
FOTO_CHECKIN = "api_legacy/images/foto_checkin"
FOTO_CHECKOUT = "api_legacy/images/foto_checkout"
MEDIA_TYPE_PNG = "image/png"

# # Original Lokasi Bengkel Teknologi Indonesia
# # Jl Gusti Hamzah No 6C Pontianak, Kalimantan Barat
# LATITUDE_BENGKOM = -0.03020289202263597
# LONGITUDE_BENGKOM = 109.3217448800716
@router.get("/get_lokasi_bengkom")
def get_lokasi_bengkom():
  return {"latitude_bengkom": LATITUDE_BENGKOM, "longitude_bengkom": LONGITUDE_BENGKOM}

@router.get("/foto_checkin/{filename}")
def get_foto_checkin(filename: str):
  img_path = os.path.join(FOTO_CHECKIN, filename)
  return FileResponse(img_path, media_type=MEDIA_TYPE_PNG)

@router.get("/foto_checkout/{filename}")
def get_foto_checkout(filename: str):
  img_path = os.path.join(FOTO_CHECKOUT, filename)
  return FileResponse(img_path, media_type=MEDIA_TYPE_PNG)

@router.get("/my_absen")
async def get_my_absen(
  month: Optional[str] = Query(None),
  year: Optional[str] = Query(None),
  user: JwtAuthorizationCredentials = Security(access_security),
):
  try:
    return await get_attendance_data(
      user=user,
      month=month,
      year=year,
    )
  
  except ValidationError as e:
    return JSONResponse(
      content={"status": "error", "message": "Validasi request gagal", "detail": e.errors()},
      status_code=422,
    )
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

@router.get("/check_in")
async def get_check_in(
  user: JwtAuthorizationCredentials = Security(access_security),
):
  try:
    return await validate_check_in_attendance(user=user)

  except ValidationError as e:
    return JSONResponse(
      content={"status": "error", "message": "Validasi request gagal", "detail": e.errors()},
      status_code=422,
    )
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
  
@router.get("/check_out")
async def get_check_out(
  user: JwtAuthorizationCredentials = Security(access_security),
):
  try:
    return await validate_check_out_attendance(user=user)

  except ValidationError as e:
    return JSONResponse(
      content={"status": "error", "message": "Validasi request gagal", "detail": e.errors()},
      status_code=422,
    )
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


@router.post("/check_in")
async def store_check_in(
  request: Request,
  background_task: BackgroundTasks,
  user: JwtAuthorizationCredentials = Security(access_security),
):
  try:
    form = await request.form()
    foto_checkin = form.get("foto_checkin")

    if not foto_checkin or not isinstance(foto_checkin, UploadFile):
      raise HTTPException(status_code=422, detail="foto_checkin wajib diisi")

    payload = CheckInRequest(
      latitude_checkin=form.get("latitude_checkin"),
      longitude_checkin=form.get("longitude_checkin"),
      pengajuan=form.get("pengajuan"),
    )

    return await store_check_in_attendance(
      payload=payload,
      photo=foto_checkin,
      background_task=background_task,
      user=user,
    )
  except ValidationError as e:
    return JSONResponse(
      content={"status": "error", "message": "Validasi request gagal", "detail": e.errors()},
      status_code=422,
    )
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

@router.put("/check_out")
async def store_check_out(
  request: Request,
  background_task: BackgroundTasks,
  user: JwtAuthorizationCredentials = Security(access_security),
):
  try:
    form = await request.form()
    foto_checkout = form.get("foto_checkout")

    if not foto_checkout or not isinstance(foto_checkout, UploadFile):
      raise HTTPException(status_code=422, detail="foto_checkout wajib diisi")

    payload = CheckOutRequest(
      latitude_checkout=form.get("latitude_checkout"),
      longitude_checkout=form.get("longitude_checkout"),
    )

    return await store_check_out_attendance(
      payload=payload,
      photo=foto_checkout,
      background_task=background_task,
      user=user,
    )

  except ValidationError as e:
    return JSONResponse(
      content={"status": "error", "message": "Validasi request gagal", "detail": e.errors()},
      status_code=422,
    )
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
