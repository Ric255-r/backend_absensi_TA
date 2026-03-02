import hashlib
from datetime import datetime

from fastapi import HTTPException
from fastapi_jwt import JwtAuthorizationCredentials

from app.core.serializer import serialize_data
from app.models import Akun
from app.schemas.requests.auth import LoginRequest
from jwt_auth import access_security, refresh_security


def _token_subject(auth_user: JwtAuthorizationCredentials | dict) -> dict:
  return auth_user.subject if hasattr(auth_user, "subject") else auth_user


async def login_user(payload: LoginRequest) -> dict:
  user_data_rows = await Akun.filter(username=payload.username).limit(1).values(
    "username",
    "passwd",
    "roles",
    "status",
    "device_id",
    "last_login",
    "karyawan_id",
    "karyawan__nama_karyawan",
    "karyawan__status",
    "karyawan__foto_profile",
  )
  user_data = user_data_rows[0] if user_data_rows else None

  if not user_data:
    raise HTTPException(status_code=404, detail="User Not Found")

  if payload.is_admin == 1 and user_data["roles"] not in ["admin", "owner"]:
    raise HTTPException(status_code=401, detail="Akses Anda Dibatasi")

  if user_data["status"] == "nonaktif":
    raise HTTPException(
      status_code=401, detail="Akun Anda Dinonaktifkan. Hubungi Admin."
    )

  if user_data["karyawan__status"] == "nonaktif":
    raise HTTPException(
      status_code=401, detail="Status Karyawan Tidak Aktif. Akses Ditolak."
    )

  req_passwd = hashlib.md5(str(payload.passwd).encode()).hexdigest()
  if req_passwd != user_data["passwd"].strip():
    raise HTTPException(status_code=401, detail="Password Salah")

  is_first_time_bind = False
  if payload.is_admin is None:
    if not payload.device_id:
      raise HTTPException(status_code=400, detail="device_id wajib untuk login mobile")

    stored_device_id = user_data.get("device_id")

    if not stored_device_id:
      user_data["device_id"] = payload.device_id
      is_first_time_bind = True
    elif payload.device_id != stored_device_id:
      raise HTTPException(status_code=401, detail="Device Anda Berbeda. Akses Dibatasi")

  token_payload = {
    "username": user_data["username"],
    "roles": user_data["roles"],
    "status": user_data["status"],
    "device_id": user_data.get("device_id"),
    "id_karyawan": user_data["karyawan_id"],
    "nama_karyawan": user_data["karyawan__nama_karyawan"],
    "foto_profile": user_data.get("karyawan__foto_profile"),
    "is_first_time_bind": is_first_time_bind,
    "last_login": user_data.get("last_login"),
  }

  access_token = access_security.create_access_token(serialize_data(token_payload))
  refresh_token = refresh_security.create_refresh_token(serialize_data(token_payload))

  if not is_first_time_bind:
    await Akun.filter(username=payload.username).update(last_login=datetime.now())

  return {
    "data_user": serialize_data(token_payload),
    "access_token": access_token,
    "refresh_token": refresh_token,
  }


async def get_current_user(
  auth_user: JwtAuthorizationCredentials,
  is_admin: bool = False,
) -> dict:
  if not auth_user:
    raise HTTPException(status_code=401, detail="Invalid token payload")
  subject = _token_subject(auth_user)

  item = await Akun.filter(karyawan_id=subject["id_karyawan"]).limit(1).values(
    "username",
    "roles",
    "status",
    "device_id",
    "last_login",
    "karyawan_id",
    "karyawan__nama_karyawan",
    "karyawan__foto_profile",
  )
  item = item[0] if item else None

  if not item:
    raise HTTPException(status_code=404, detail="User Not Found in DB")

  if not is_admin:
    device_id_from_token = subject.get("device_id")
    if item.get("device_id") != device_id_from_token:
      raise HTTPException(
        status_code=401,
        detail="Device binding berubah. Silakan login kembali.",
      )

  return serialize_data(item)


async def confirm_bind(auth_user: JwtAuthorizationCredentials) -> dict:
  subject = _token_subject(auth_user)
  username = subject.get("username")
  device_id = subject.get("device_id")

  if not username or not device_id:
    raise HTTPException(status_code=401, detail="Token tidak valid")

  updated = await Akun.filter(username=username, device_id__isnull=True).update(
    device_id=device_id,
    last_login=datetime.now(),
  )

  if updated == 0:
    raise HTTPException(status_code=409, detail="Akun sudah ter-bind.")

  return {"status": "ok", "message": "Device berhasil di-bind"}


async def refresh_user_token(auth_user: JwtAuthorizationCredentials) -> dict:
  if not auth_user:
    raise HTTPException(status_code=401, detail="Invalid token payload")
  subject = _token_subject(auth_user)

  item = await Akun.filter(karyawan_id=subject["id_karyawan"]).limit(1).values(
    "username",
    "roles",
    "status",
    "device_id",
    "last_login",
    "karyawan_id",
    "karyawan__nama_karyawan",
    "karyawan__status",
    "karyawan__foto_profile",
  )
  item = item[0] if item else None

  if not item:
    raise HTTPException(status_code=404, detail="User Not Found in DB")

  if item["status"] == "nonaktif":
    raise HTTPException(
      status_code=401, detail="Akun Anda Dinonaktifkan. Hubungi Admin."
    )

  if item["karyawan__status"] == "nonaktif":
    raise HTTPException(
      status_code=401, detail="Status Karyawan Tidak Aktif. Akses Ditolak."
    )

  device_id_from_token = subject.get("device_id")
  if item.get("device_id") != device_id_from_token:
    raise HTTPException(
      status_code=401,
      detail="Device binding berubah. Silakan login kembali.",
    )

  token_payload = {
    "username": item["username"],
    "roles": item["roles"],
    "status": item["status"],
    "device_id": item.get("device_id"),
    "id_karyawan": item["karyawan_id"],
    "nama_karyawan": item["karyawan__nama_karyawan"],
    "foto_profile": item.get("karyawan__foto_profile"),
    "is_first_time_bind": False,
    "last_login": item.get("last_login"),
  }

  access_token = access_security.create_access_token(serialize_data(token_payload))
  refresh_token = refresh_security.create_refresh_token(serialize_data(token_payload))

  await Akun.filter(username=item["username"]).update(last_login=datetime.now())

  return {
    "data_user": serialize_data(token_payload),
    "access_token": access_token,
    "refresh_token": refresh_token,
  }
