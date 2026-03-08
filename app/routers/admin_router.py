from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_jwt import JwtAuthorizationCredentials
from fastapi.responses import JSONResponse

from app.controllers import admin_controller
from app.core.audit import enable_audit, set_audit_actor
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
from app.schemas.responses import (
  AkunItemResponse,
  APIMessage,
  DataDashboardResponse,
  DepartemenItemResponse,
  HariLiburResponse,
  JadwalItemResponse,
  KaryawanItemResponse,
  KonfigurasiItemResponse,
  PengajuanItemResponse,
)
from jwt_auth import verify_jwt


async def verify_jwt_admin(user: JwtAuthorizationCredentials = Depends(verify_jwt)):
  enable_audit(True)
  set_audit_actor(user)
  return user


router = APIRouter(
  prefix="/admin",
  tags=["Admin"],
  dependencies=[Depends(verify_jwt_admin)],
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


@router.get(
  "/get_karyawan",
  response_model=KaryawanItemResponse | list[KaryawanItemResponse] | None,
)
async def get_karyawan(id_karyawan: str | None = Query(None)):
  try:
    return await admin_controller.get_karyawan(id_karyawan=id_karyawan)
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/get_akun", response_model=list[AkunItemResponse])
async def get_akun():
  try:
    return await admin_controller.get_akun()
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/get_exists_akun", response_model=list[AkunItemResponse])
async def get_exists_akun(username: str):
  try:
    return await admin_controller.get_akun(username=username)
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/get_departemen", response_model=list[DepartemenItemResponse])
async def get_departemen():
  try:
    return await admin_controller.get_departemen()
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/get_jadwal", response_model=list[JadwalItemResponse])
async def get_jadwal():
  try:
    return await admin_controller.get_jadwal()
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/get_konfigurasi", response_model=KonfigurasiItemResponse | None)
async def get_konfigurasi():
  try:
    return await admin_controller.get_konfigurasi()
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/get_data_dashboard", response_model=DataDashboardResponse)
async def get_data_dashboard(tgl: str | None = Query(None)):
  try:
    return await admin_controller.get_data_dashboard(tgl=tgl)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/get_analytics")
async def get_analytics(
  start_date: str | None = Query(None),
  end_date: str | None = Query(None),
):
  try:
    return await admin_controller.get_analytics(
      start_date=start_date, end_date=end_date
    )
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/get_pengajuan", response_model=list[PengajuanItemResponse])
async def get_pengajuan(tgl: str | None = Query(None)):
  try:
    return await admin_controller.get_pengajuan(tgl=tgl)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
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
async def update_karyawan(
  id_karyawan: str,
  payload: KaryawanUpdateRequest,
  user: JwtAuthorizationCredentials = Depends(verify_jwt_admin),
):
  try:
    return await admin_controller.update_karyawan(id_karyawan, payload, actor=user)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/update_akun", response_model=APIMessage)
async def update_akun(
  username: str,
  payload: AkunUpdateRequest,
  user: JwtAuthorizationCredentials = Depends(verify_jwt_admin),
):
  try:
    return await admin_controller.update_akun(username, payload, actor=user)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/update_konfigurasi", response_model=APIMessage)
async def update_konfigurasi(
  payload: KonfigurasiUpdateRequest,
  user: JwtAuthorizationCredentials = Depends(verify_jwt_admin),
):
  try:
    return await admin_controller.update_konfigurasi(payload, actor=user)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/update_jadwal/{id_jadwal}", response_model=APIMessage)
async def update_jadwal(
  id_jadwal: int,
  payload: JadwalUpdateRequest,
  user: JwtAuthorizationCredentials = Depends(verify_jwt_admin),
):
  try:
    return await admin_controller.update_jadwal(id_jadwal, payload, actor=user)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/hari_libur/{id_libur}", response_model=APIMessage)
async def update_hari_libur(
  id_libur: int,
  payload: HariLiburUpdateRequest,
  user: JwtAuthorizationCredentials = Depends(verify_jwt_admin),
):
  try:
    return await admin_controller.update_hari_libur(id_libur, payload, actor=user)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/unbind_device/{username}", response_model=APIMessage)
async def unbind_device(
  username: str,
  user: JwtAuthorizationCredentials = Depends(verify_jwt_admin),
):
  try:
    return await admin_controller.unbind_device(username, actor=user)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/update_status_absensi", response_model=APIMessage)
async def update_status_absensi(
  payload: UpdateStatusAbsensiRequest,
  user: JwtAuthorizationCredentials = Depends(verify_jwt_admin),
):
  try:
    return await admin_controller.update_status_absensi(payload, actor=user)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.put("/update_pengajuan", response_model=APIMessage)
async def update_pengajuan(
  payload: UpdatePengajuanRequest,
  user: JwtAuthorizationCredentials = Depends(verify_jwt_admin),
):
  try:
    return await admin_controller.update_pengajuan(payload, actor=user)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.delete("/delete_karyawan/{id_karyawan}", response_model=APIMessage)
async def delete_karyawan(
  id_karyawan: str,
  user: JwtAuthorizationCredentials = Depends(verify_jwt_admin),
):
  try:
    return await admin_controller.delete_karyawan(id_karyawan, actor=user)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.delete("/delete_akun/{username}", response_model=APIMessage)
async def delete_akun(
  username: str,
  user: JwtAuthorizationCredentials = Depends(verify_jwt_admin),
):
  try:
    return await admin_controller.delete_akun(username, actor=user)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.delete("/delete_departemen/{id_departemen}", response_model=APIMessage)
async def delete_departemen(
  id_departemen: int,
  user: JwtAuthorizationCredentials = Depends(verify_jwt_admin),
):
  try:
    return await admin_controller.delete_departemen(id_departemen, actor=user)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.delete("/hari_libur/{id_libur}", response_model=APIMessage)
async def delete_hari_libur(
  id_libur: int,
  user: JwtAuthorizationCredentials = Depends(verify_jwt_admin),
):
  try:
    return await admin_controller.delete_hari_libur(id_libur, actor=user)
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail}, status_code=e.status_code
    )
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
