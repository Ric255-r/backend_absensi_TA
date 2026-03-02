from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.controllers import admin_controller
from app.schemas.requests.admin import (
  AkunCreateRequest,
  AkunUpdateRequest,
  DepartemenCreateRequest,
  JadwalUpdateRequest,
  KaryawanCreateRequest,
  KaryawanUpdateRequest,
  KonfigurasiUpdateRequest,
)
from jwt_auth import verify_jwt

router = APIRouter(
  prefix="/admin",
  tags=["Admin"],
  dependencies=[Depends(verify_jwt)],
)


@router.post("/regis_karyawan")
async def regis_karyawan(payload: KaryawanCreateRequest):
  try:
    return await admin_controller.regis_karyawan(payload)
  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": str(e)},
      status_code=500,
    )


@router.post("/regis_akun")
async def regis_akun(payload: AkunCreateRequest):
  try:
    return await admin_controller.regis_akun(payload)
  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": str(e)},
      status_code=500,
    )


@router.post("/regis_departemen")
async def regis_departemen(payload: DepartemenCreateRequest):
  try:
    return await admin_controller.regis_departemen(payload)
  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": str(e)},
      status_code=500,
    )


@router.get("/get_karyawan")
async def get_karyawan(id_karyawan: str | None = Query(None)):
  try:
    return await admin_controller.get_karyawan(id_karyawan=id_karyawan)
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/get_akun")
async def get_akun():
  try:
    return await admin_controller.get_akun()
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/get_exists_akun")
async def get_exists_akun(username: str):
  try:
    return await admin_controller.get_akun(username=username)
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/get_departemen")
async def get_departemen():
  try:
    return await admin_controller.get_departemen()
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/get_jadwal")
async def get_jadwal():
  try:
    return await admin_controller.get_jadwal()
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/get_konfigurasi")
async def get_konfigurasi():
  try:
    return await admin_controller.get_konfigurasi()
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/update_karyawan")
async def update_karyawan(id_karyawan: str, payload: KaryawanUpdateRequest):
  try:
    return await admin_controller.update_karyawan(id_karyawan, payload)
  except HTTPException as e:
    return JSONResponse(content={"status": "error", "message": e.detail}, status_code=e.status_code)
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/update_akun")
async def update_akun(username: str, payload: AkunUpdateRequest):
  try:
    return await admin_controller.update_akun(username, payload)
  except HTTPException as e:
    return JSONResponse(content={"status": "error", "message": e.detail}, status_code=e.status_code)
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/update_konfigurasi")
async def update_konfigurasi(id_pengaturan: int, payload: KonfigurasiUpdateRequest):
  try:
    return await admin_controller.update_konfigurasi(id_pengaturan, payload)
  except HTTPException as e:
    return JSONResponse(content={"status": "error", "message": e.detail}, status_code=e.status_code)
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/update_jadwal/{id_jadwal}")
async def update_jadwal(id_jadwal: int, payload: JadwalUpdateRequest):
  try:
    return await admin_controller.update_jadwal(id_jadwal, payload)
  except HTTPException as e:
    return JSONResponse(content={"status": "error", "message": e.detail}, status_code=e.status_code)
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/unbind_device/{username}")
async def unbind_device(username: str):
  try:
    return await admin_controller.unbind_device(username)
  except HTTPException as e:
    return JSONResponse(content={"status": "error", "message": e.detail}, status_code=e.status_code)
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.delete("/delete_karyawan/{id_karyawan}")
async def delete_karyawan(id_karyawan: str):
  try:
    return await admin_controller.delete_karyawan(id_karyawan)
  except HTTPException as e:
    return JSONResponse(content={"status": "error", "message": e.detail}, status_code=e.status_code)
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.delete("/delete_akun/{username}")
async def delete_akun(username: str):
  try:
    return await admin_controller.delete_akun(username)
  except HTTPException as e:
    return JSONResponse(content={"status": "error", "message": e.detail}, status_code=e.status_code)
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.delete("/delete_departemen/{id_departemen}")
async def delete_departemen(id_departemen: int):
  try:
    return await admin_controller.delete_departemen(id_departemen)
  except HTTPException as e:
    return JSONResponse(content={"status": "error", "message": e.detail}, status_code=e.status_code)
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

