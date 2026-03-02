import hashlib
from datetime import date, datetime, time

from fastapi import HTTPException
from tortoise import Tortoise

from app.models import Akun, Departemen, JadwalKerja, Karyawan, KonfigurasiAplikasi
from app.schemas.requests.admin import (
  AkunCreateRequest,
  AkunUpdateRequest,
  DepartemenCreateRequest,
  JadwalUpdateRequest,
  KaryawanCreateRequest,
  KaryawanUpdateRequest,
  KonfigurasiUpdateRequest,
)


async def regis_karyawan(payload: KaryawanCreateRequest) -> dict:
  tanggal_rekrut = (
    date.fromisoformat(payload.tanggal_rekrut) if payload.tanggal_rekrut else None
  )

  await Karyawan.create(
    id_karyawan=payload.id_karyawan,
    nama_karyawan=payload.nama_karyawan,
    email_karyawan=payload.email_karyawan,
    nomor_hp=payload.nomor_hp,
    tanggal_rekrut=tanggal_rekrut,
    status=payload.status,
    departemen_id=payload.id_departemen,
    posisi=payload.posisi,
  )
  return {"status": "ok", "message": "Sukses Simpan Data"}


async def regis_akun(payload: AkunCreateRequest) -> dict:
  passwd = hashlib.md5(str(payload.passwd).encode()).hexdigest()
  await Akun.create(
    username=payload.username,
    passwd=passwd,
    roles=payload.roles,
    karyawan_id=payload.id_karyawan,
    status=payload.status,
  )
  return {"status": "ok", "message": "Sukses Simpan Data"}


async def regis_departemen(payload: DepartemenCreateRequest) -> dict:
  await Departemen.create(nama_departemen=payload.nama_departemen)
  return {"status": "ok", "message": "Sukses Simpan Data"}


async def get_karyawan(id_karyawan: str | None = None):
  query = Karyawan.all()
  if id_karyawan:
    items = await query.filter(id_karyawan=id_karyawan).limit(1).values(
      "id_karyawan",
      "nama_karyawan",
      "email_karyawan",
      "nomor_hp",
      "foto_profile",
      "tanggal_rekrut",
      "status",
      "posisi",
      "departemen_id",
      "departemen__nama_departemen",
    )
    return items[0] if items else None
  return await query.values(
    "id_karyawan",
    "nama_karyawan",
    "email_karyawan",
    "nomor_hp",
    "foto_profile",
    "tanggal_rekrut",
    "status",
    "posisi",
    "departemen_id",
    "departemen__nama_departemen",
  )


async def get_akun(username: str | None = None):
  query = Akun.all()
  if username:
    items = await query.filter(username=username).limit(1).values(
      "username",
      "roles",
      "status",
      "last_login",
      "device_id",
      "karyawan_id",
    )
    item = items[0] if items else None
    return [item] if item else []
  return await query.values(
    "username",
    "roles",
    "status",
    "last_login",
    "device_id",
    "karyawan_id",
  )


async def get_departemen():
  return await Departemen.all().values("id_departemen", "nama_departemen")


async def get_jadwal():
  return await JadwalKerja.all().values(
    "id_jadwal", "hari_dalam_seminggu", "shift_mulai", "shift_selesai"
  )


async def get_konfigurasi():
  items = await KonfigurasiAplikasi.all().order_by("id_pengaturan").limit(1).values(
    "id_pengaturan", "toleransi_terlambat", "maks_hari_cuti"
  )
  return items[0] if items else None


async def get_hari_libur():
  conn = Tortoise.get_connection("default")
  return await conn.execute_query_dict("SELECT * FROM hari_libur")


async def update_karyawan(id_karyawan: str, payload: KaryawanUpdateRequest) -> dict:
  tanggal_rekrut = (
    date.fromisoformat(payload.tanggal_rekrut) if payload.tanggal_rekrut else None
  )

  updated = await Karyawan.filter(id_karyawan=id_karyawan).update(
    nama_karyawan=payload.nama_karyawan,
    email_karyawan=payload.email_karyawan,
    nomor_hp=payload.nomor_hp,
    tanggal_rekrut=tanggal_rekrut,
    status=payload.status,
    departemen_id=payload.id_departemen,
    posisi=payload.posisi,
  )
  if updated == 0:
    raise HTTPException(status_code=404, detail="Data karyawan tidak ditemukan")

  return {"status": "ok", "message": "Sukses Simpan Data"}


async def update_akun(username: str, payload: AkunUpdateRequest) -> dict:
  passwd = hashlib.md5(str(payload.passwd).encode()).hexdigest()
  status = "aktif" if payload.status else "nonaktif"

  updated = await Akun.filter(username=username).update(
    passwd=passwd,
    roles=payload.roles,
    karyawan_id=payload.id_karyawan,
    status=status,
  )
  if updated == 0:
    raise HTTPException(status_code=404, detail="Data akun tidak ditemukan")

  return {"status": "ok", "message": "Sukses Simpan Data"}


async def update_konfigurasi(
  id_pengaturan: int,
  payload: KonfigurasiUpdateRequest,
) -> dict:
  updated = await KonfigurasiAplikasi.filter(id_pengaturan=id_pengaturan).update(
    toleransi_terlambat=payload.toleransi_terlambat,
    maks_hari_cuti=payload.maks_hari_cuti,
  )
  if updated == 0:
    raise HTTPException(status_code=404, detail="Konfigurasi tidak ditemukan")

  return {"status": "ok", "message": "Sukses Simpan Data"}


async def update_jadwal(id_jadwal: int, payload: JadwalUpdateRequest) -> dict:
  fields_to_update = {}
  if payload.shift_mulai:
    fields_to_update["shift_mulai"] = time.fromisoformat(payload.shift_mulai)
  if payload.shift_selesai:
    fields_to_update["shift_selesai"] = time.fromisoformat(payload.shift_selesai)

  if not fields_to_update:
    raise HTTPException(status_code=400, detail="Tidak ada field jadwal yang diupdate")

  updated = await JadwalKerja.filter(id_jadwal=id_jadwal).update(**fields_to_update)
  if updated == 0:
    raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan")

  return {"status": "ok", "message": "Sukses Simpan Data"}


async def unbind_device(username: str) -> dict:
  updated = await Akun.filter(username=username).update(device_id=None)
  if updated == 0:
    raise HTTPException(status_code=404, detail="Akun tidak ditemukan")
  return {"status": "ok", "message": "Sukses Unbind Device Data"}


async def delete_karyawan(id_karyawan: str) -> dict:
  deleted = await Karyawan.filter(id_karyawan=id_karyawan).delete()
  if deleted == 0:
    raise HTTPException(status_code=404, detail="Data karyawan tidak ditemukan")
  return {"status": "ok", "message": "Sukses Delete Data"}


async def delete_akun(username: str) -> dict:
  deleted = await Akun.filter(username=username).delete()
  if deleted == 0:
    raise HTTPException(status_code=404, detail="Data akun tidak ditemukan")
  return {"status": "ok", "message": "Sukses Delete Data"}


async def delete_departemen(id_departemen: int) -> dict:
  deleted = await Departemen.filter(id_departemen=id_departemen).delete()
  if deleted == 0:
    raise HTTPException(status_code=404, detail="Data departemen tidak ditemukan")
  return {"status": "ok", "message": "Sukses Delete Data"}
