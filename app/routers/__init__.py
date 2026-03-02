from fastapi import APIRouter

from app.routers.absensi_router import router as absensi_router
from app.routers.admin_router import router as admin_router
from app.routers.admin_ws_router import router as admin_ws_router
from app.routers.auth_router import router as auth_router
from app.routers.user_router import router as user_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(admin_ws_router)
api_router.include_router(admin_router)
api_router.include_router(user_router)
api_router.include_router(absensi_router)
