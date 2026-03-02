from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime.absensi_ws import absensi_connections, admin_to_user_conn

router = APIRouter(prefix="/admin", tags=["AdminWS"])


@router.websocket("/ws-absensi")
async def ws_absensi(websocket: WebSocket):
  await websocket.accept()
  absensi_connections.append(websocket)

  try:
    await websocket.receive_text()
  except WebSocketDisconnect:
    if websocket in absensi_connections:
      absensi_connections.remove(websocket)


@router.websocket("/ws-user")
async def ws_absen_user(websocket: WebSocket):
  await websocket.accept()
  admin_to_user_conn.append(websocket)

  try:
    print("Hai WS Nyala")
    await websocket.receive_text()
  except WebSocketDisconnect:
    print("WS Disconnect")
    admin_to_user_conn.remove(websocket)