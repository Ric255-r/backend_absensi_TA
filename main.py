from fastapi import FastAPI
from fastapi import APIRouter
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.database import init_tortoise
from app.routers import api_router
from api_legacy.admin.delete_data import app as legacy_delete_admin
from api_legacy.admin.get_data import app as legacy_get_data
from api_legacy.admin.regis_data import app as legacy_regis
from api_legacy.admin.update_data import app as legacy_update_admin
from api_legacy.admin.update_pengajuan import app as legacy_update_pengajuan
from api_legacy.users.absen_tidakhadir import app as legacy_tidakhadir
from api_legacy.users.absensi import app as legacy_absensi
from api_legacy.users.update_profile import app as legacy_profile_user
from services.login import app as legacy_login
from services.seeder import app as legacy_seeder
from utils.logging_config import app_logger, configure_uvicorn_logging, error_logger

configure_uvicorn_logging()

app = FastAPI()
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],  # or specify list like ["http://localhost:5173"]
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
  error_logger.exception(
    "Unhandled exception on %s %s",
    request.method,
    request.url.path,
  )
  return JSONResponse(
    status_code=500,
    content={"detail": "Internal Server Error"},
  )


init_tortoise(app)
app.include_router(api_router)

# Legacy compatibility during migration to Tortoise ORM architecture.
legacy_router = APIRouter(prefix="/api/legacy")
legacy_router.include_router(legacy_login)
legacy_router.include_router(legacy_regis)
legacy_router.include_router(legacy_absensi)
legacy_router.include_router(legacy_tidakhadir)
legacy_router.include_router(legacy_get_data)
legacy_router.include_router(legacy_update_pengajuan)
legacy_router.include_router(legacy_delete_admin)
legacy_router.include_router(legacy_update_admin)
legacy_router.include_router(legacy_profile_user)
legacy_router.include_router(legacy_seeder)
app.include_router(legacy_router)

app_logger.info("Application routes loaded")

# bawaan default
if __name__ == "__main__":
  import uvicorn

  uvicorn.run(app, host="0.0.0.0", port=5500)
