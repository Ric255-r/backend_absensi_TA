from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.controllers.subscription_controller import expire_subscription_job
from app.dependencies import verify_internal_job_token

router = APIRouter(prefix="/internal", tags=["Internal"])


@router.post(
  "/subscriptions/expire",
  dependencies=[Depends(verify_internal_job_token)],
)
async def run_expire_subscription_job():
  try:
    return await expire_subscription_job()
  except HTTPException as e:
    return JSONResponse(
      content={"status": "error", "message": e.detail},
      status_code=e.status_code,
    )
  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": str(e)},
      status_code=500,
    )
