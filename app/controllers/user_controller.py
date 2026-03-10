import hashlib
import os
import uuid

from fastapi import HTTPException, UploadFile
from fastapi_jwt import JwtAuthorizationCredentials

from app.models import Akun, Karyawan
from app.schemas.requests.auth import PasswordUpdateRequest

FOTO_PROFILE = "api_legacy/images/foto_profile"


def save_upload_file(upload: UploadFile, dest: str):
  with open(dest, "wb") as f:
    f.write(upload.file.read())


async def update_profile(form_data: dict, user: JwtAuthorizationCredentials) -> dict:
  filename = None
  if "foto_profile" in form_data and form_data["foto_profile"]:
    filename = f"{uuid.uuid4()}.png"
    file_location = os.path.join(FOTO_PROFILE, filename)
    save_upload_file(form_data["foto_profile"], file_location)

  """
  Bukan pointer. Di Python, ** pada update(**update_data) adalah operator untuk 
  dictionary unpacking. Artinya isi dict ini, akan diurai 
  menjadi spt ini pada method update ORM: 
  update(
    nama_karyawan=...,
    email_karyawan=...,
    nomor_hp=...,
  )
  """
  update_data = {
    "nama_karyawan": form_data.get("nama_karyawan"),
    "email_karyawan": form_data.get("email_karyawan"),
    "nomor_hp": form_data.get("nomor_hp"),
  }

  if filename:
    update_data["foto_profile"] = filename

  updated = await Karyawan.filter(id_karyawan=user["id_karyawan"]).update(**update_data)
  if updated == 0:
    raise HTTPException(status_code=404, detail="Data karyawan tidak ditemukan")

  return {"status": "ok", "message": "Sukses Simpan Data"}


async def update_password(
  payload: PasswordUpdateRequest, user: JwtAuthorizationCredentials
) -> dict:
  account = await Akun.get_or_none(karyawan_id=user["id_karyawan"])
  if not account:
    raise HTTPException(status_code=404, detail="Akun tidak ditemukan")

  old_pass = hashlib.md5(str(payload.old_pass).encode()).hexdigest()
  if old_pass != account.passwd:
    raise HTTPException(status_code=403, detail="Password Anda Salah")

  new_pass = hashlib.md5(str(payload.new_pass).encode()).hexdigest()
  await Akun.filter(karyawan_id=user["id_karyawan"]).update(passwd=new_pass)

  return {"status": "ok", "message": "Sukses Simpan Data"}
