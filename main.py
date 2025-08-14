import asyncio
import os
import ipaddress
from fastapi import Depends, FastAPI, APIRouter, Request, Security, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_jwt import JwtAuthorizationCredentials
from services.login import app as app_karyawan
from api.admin.regis_data import app as app_regis
from api.admin.get_data import app as app_get_data
from api.admin.update_pengajuan import app as app_update_pengajuan
from api.admin.update_data import app as app_update_admin
from api.admin.delete_data import app as app_delete_admin
from api.users.absensi import app as app_absensi
from api.users.absen_tidakhadir import app as app_tidakhadir
from api.users.update_profile import app as app_profile_user
from jwt_auth import access_security

from koneksi import lifespan
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(lifespan=lifespan)
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],  # or specify list like ["http://localhost:5173"]
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

main_router = APIRouter()

main_router.include_router(app_karyawan)
main_router.include_router(app_regis)
main_router.include_router(app_absensi)
main_router.include_router(app_tidakhadir)
main_router.include_router(app_get_data)
main_router.include_router(app_update_pengajuan)
main_router.include_router(app_delete_admin)
main_router.include_router(app_update_admin)
main_router.include_router(app_profile_user)

#masukkan main router ke fastapi app
app.include_router(main_router, prefix="/api")

# bawaan default
if __name__ == "__main__":
  import uvicorn

  # Cara jalanin dgn Reload
  # uvicorn main:app --reload --host 192.168.100.11 --port 5500
  uvicorn.run(app, host="100.101.128.60", port=5500)

  # uvicorn main:app --host 0.0.0.0 --port 5500 --workers 4
