from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.controllers import admin_controller
from app.schemas.requests.admin import (
  AkunCreateRequest,
  AkunUpdateRequest,
  DepartemenCreateRequest,
  HariLiburCreateRequest,
  HariLiburUpdateRequest,
  JadwalUpdateRequest,
  KaryawanCreateRequest,
  KaryawanUpdateRequest,
  KonfigurasiUpdateRequest,
  UpdatePengajuanRequest,
  UpdateStatusAbsensiRequest,
)
from app.schemas.responses import APIMessage, HariLiburResponse
from jwt_auth import verify_jwt

router = APIRouter(
  prefix="/admin",
  tags=["Admin"],
  dependencies=[Depends(verify_jwt)],
)


@router.post("/regis_karyawan", response_model=APIMessage)
async def regis_karyawan(payload: KaryawanCreateRequest):
  try:
    return await admin_controller.regis_karyawan(payload)
  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": str(e)},
      status_code=500,
    )


@router.post("/regis_akun", response_model=APIMessage)
async def regis_akun(payload: AkunCreateRequest):
  try:
    return await admin_controller.regis_akun(payload)
  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": str(e)},
      status_code=500,
    )


@router.post("/regis_departemen", response_model=APIMessage)
async def regis_departemen(payload: DepartemenCreateRequest):
  try:
    return await admin_controller.regis_departemen(payload)
  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": str(e)},
      status_code=500,
    )


@router.post("/hari_libur", response_model=APIMessage)
async def regis_hari_libur(payload: HariLiburCreateRequest):
  try:
    return await admin_controller.regis_hari_libur(payload)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


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


@router.get("/hari_libur", response_model=list[HariLiburResponse])
async def get_hari_libur():
  try:
    return await admin_controller.get_hari_libur()
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/export_excel")
async def export_excel(
  start_date: str | None = Query(None),
  end_date: str | None = Query(None),
):
  try:
    return await admin_controller.export_excel(start_date=start_date, end_date=end_date)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/update_karyawan", response_model=APIMessage)
async def update_karyawan(id_karyawan: str, payload: KaryawanUpdateRequest):
  try:
    return await admin_controller.update_karyawan(id_karyawan, payload)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/update_akun", response_model=APIMessage)
async def update_akun(username: str, payload: AkunUpdateRequest):
  try:
    return await admin_controller.update_akun(username, payload)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/update_konfigurasi", response_model=APIMessage)
async def update_konfigurasi(id_pengaturan: int, payload: KonfigurasiUpdateRequest):
  try:
    return await admin_controller.update_konfigurasi(id_pengaturan, payload)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/update_jadwal/{id_jadwal}", response_model=APIMessage)
async def update_jadwal(id_jadwal: int, payload: JadwalUpdateRequest):
  try:
    return await admin_controller.update_jadwal(id_jadwal, payload)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/hari_libur/{id_libur}", response_model=APIMessage)
async def update_hari_libur(id_libur: int, payload: HariLiburUpdateRequest):
  try:
    return await admin_controller.update_hari_libur(id_libur, payload)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/unbind_device/{username}", response_model=APIMessage)
async def unbind_device(username: str):
  try:
    return await admin_controller.unbind_device(username)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
  
@router.put("/update_status_absensi", response_model=APIMessage)
async def update_status_absensi(payload: UpdateStatusAbsensiRequest):
  try:
    return await admin_controller.update_status_absensi(payload)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/update_pengajuan", response_model=APIMessage)
async def update_pengajuan(payload: UpdatePengajuanRequest):
  try:
    return await admin_controller.update_pengajuan(payload)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.delete("/delete_karyawan/{id_karyawan}", response_model=APIMessage)
async def delete_karyawan(id_karyawan: str):
  try:
    return await admin_controller.delete_karyawan(id_karyawan)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.delete("/delete_akun/{username}", response_model=APIMessage)
async def delete_akun(username: str):
  try:
    return await admin_controller.delete_akun(username)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.delete("/delete_departemen/{id_departemen}", response_model=APIMessage)
async def delete_departemen(id_departemen: int):
  try:
    return await admin_controller.delete_departemen(id_departemen)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.delete("/hari_libur/{id_libur}", response_model=APIMessage)
async def delete_hari_libur(id_libur: int):
  try:
    return await admin_controller.delete_hari_libur(id_libur)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
