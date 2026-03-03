import hashlib
from datetime import date, datetime, time, timedelta
import json

from fastapi import HTTPException

from app.models import (
  Akun,
  Departemen,
  HariLibur,
  JadwalKerja,
  Karyawan,
  KonfigurasiAplikasi,
  PengajuanAbsen,
)
from app.models.absensi import Absensi
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
from utils.fn_log import logger
from app.realtime.absensi_ws import admin_to_user_conn
from tortoise.transactions import in_transaction


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


async def regis_hari_libur(payload: HariLiburCreateRequest) -> dict:
  await HariLibur.create(
    tanggal=date.fromisoformat(payload.tanggal),
    keterangan=payload.keterangan,
    tipe=payload.tipe,
  )
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
  return await HariLibur.all().order_by("tanggal").values(
    "id_libur", "tanggal", "keterangan", "tipe"
  )


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


async def update_hari_libur(id_libur: int, payload: HariLiburUpdateRequest) -> dict:
  updated = await HariLibur.filter(id_libur=id_libur).update(
    tanggal=date.fromisoformat(payload.tanggal),
    keterangan=payload.keterangan,
    tipe=payload.tipe,
  )
  if updated == 0:
    raise HTTPException(status_code=404, detail="Data hari libur tidak ditemukan")

  return {"status": "ok", "message": "Sukses Update Data"}

async def update_status_absensi(
  payload: UpdateStatusAbsensiRequest,
  is_bulk: bool = False,
):
  # print ku sementara buat pengganti log_message yang ada di legacy.
  if is_bulk and payload.updated_bulk_data:
    for item in payload.updated_bulk_data:
      if item.get("status_absen") == "rejected":
        print("Alasan Penolakan:", item.get("alasan_penolakan", "Tidak ada alasan yang diberikan"))
        log_message = (
          f"Karyawan [{item.get('id_karyawan')}] Sudah Di Reject. Skipped From Bulk"
        )
        logger.info(log_message)
        continue

      await Absensi.filter(id_absensi=item["id_absensi"], karyawan_id=item["id_karyawan"]).update(
        status_absen=item["status_absen"],
        alasan_penolakan=item.get("alasan_penolakan", None),
      )
      log_message = (
        f"ADMIN  MENGUPDATE STATUS ABSENSI untuk Karyawan [{item['id_karyawan']}] "
        f"menjadi [{item['status_absen']}]"
      )
      logger.info(log_message)

      for ws_con in admin_to_user_conn:
        await ws_con.send_text(
          json.dumps(
            {
              "id_karyawan": item["id_karyawan"],
              "status": item["status_absen"],
              "message": f"Absen Anda di{item['status_absen']}",
            }
          )
        )
  else:
    await Absensi.filter(id_absensi=payload.id_absensi, karyawan_id=payload.id_karyawan).update(
      status_absen=payload.status_absen,
      alasan_penolakan=payload.alasan_penolakan if payload.alasan_penolakan else None,
    )
    log_message = (
      f"ADMIN  MENGUPDATE STATUS ABSENSI untuk Karyawan [{payload.id_karyawan}] "
      f"menjadi [{payload.status_absen}]"
    )
    logger.info(log_message)
    for ws_con in admin_to_user_conn:
      await ws_con.send_text(
        json.dumps(
          {
            "id_karyawan": payload.id_karyawan,
            "status": payload.status_absen,
            "message": f"Absen Anda di{payload.status_absen}",
          }
        )
      )
      
  return {"status": "ok", "message": "Sukses Update Status Absensi"}


def _daterange_inclusive(d1: date, d2: date):
  cur = d1
  while cur <= d2:
    yield cur
    cur += timedelta(days=1)


async def update_pengajuan(payload: UpdatePengajuanRequest) -> dict:
  async with in_transaction() as db:
    if payload.alasan_penolakan is not None:
      updated = await PengajuanAbsen.filter(
        id_pengajuan=payload.id_pengajuan,
        karyawan_id=payload.id_karyawan,
      ).using_db(db).update(
        status=payload.status,
        alasan_penolakan=payload.alasan_penolakan,
      )
      if updated == 0:
        raise HTTPException(status_code=404, detail="Data pengajuan tidak ditemukan")

    elif payload.status == "approved":
      start_d = datetime.strptime(payload.tanggal_mulai, "%Y-%m-%d").date()
      end_d = datetime.strptime(payload.tanggal_akhir, "%Y-%m-%d").date()

      if end_d < start_d:
        raise HTTPException(status_code=400, detail="Tanggal Akhir < Tanggal Mulai")

      days_in_range = list(_daterange_inclusive(start_d, end_d))
      day_start = datetime.combine(start_d, time.min)
      day_end = datetime.combine(end_d + timedelta(days=1), time.min)

      existing_rows = await Absensi.filter(
        karyawan_id=payload.id_karyawan,
        tanggal_absen__gte=day_start,
        tanggal_absen__lt=day_end,
      ).using_db(db).values("id_absensi", "tanggal_absen")
      existing_dates = {row["tanggal_absen"].date(): row["id_absensi"] for row in existing_rows}

      for current_date in days_in_range:
        absensi_id = existing_dates.get(current_date)
        if absensi_id:
          await Absensi.filter(id_absensi=absensi_id).using_db(db).update(
            status_absen=payload.status
          )
          continue

        check_in_date = datetime.combine(current_date, time.min)
        await Absensi.create(
          karyawan_id=payload.id_karyawan,
          tanggal_absen=check_in_date,
          check_in=check_in_date,
          latitude_checkin=0.0,
          longitude_checkin=0.0,
          foto_checkin="no-foto",
          pengajuan=payload.tipe_pengajuan,
          status_absen=payload.status,
          using_db=db,
        )

      updated = await PengajuanAbsen.filter(
        id_pengajuan=payload.id_pengajuan,
        karyawan_id=payload.id_karyawan,
      ).using_db(db).update(status=payload.status)
      if updated == 0:
        raise HTTPException(status_code=404, detail="Data pengajuan tidak ditemukan")

    else:
      updated = await PengajuanAbsen.filter(
        id_pengajuan=payload.id_pengajuan,
        karyawan_id=payload.id_karyawan,
      ).using_db(db).update(status=payload.status)
      if updated == 0:
        raise HTTPException(status_code=404, detail="Data pengajuan tidak ditemukan")

  log_message = (
    f"ADMIN MENGUPDATE STATUS PENGAJUAN untuk Karyawan [{payload.id_karyawan}] "
    f"menjadi [{payload.status}]"
  )
  logger.info(log_message)

  for ws_con in admin_to_user_conn:
    await ws_con.send_text(
      json.dumps(
        {
          "id_karyawan": payload.id_karyawan,
          "status": payload.status,
          "message": f"Pengajuan Anda telah di-{payload.status}",
        }
      )
    )

  return {"status": "ok", "message": "Sukses Update Pengajuan"}


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


async def delete_hari_libur(id_libur: int) -> dict:
  deleted = await HariLibur.filter(id_libur=id_libur).delete()
  if deleted == 0:
    raise HTTPException(status_code=404, detail="Data hari libur tidak ditemukan")
  return {"status": "ok", "message": "Sukses Delete Data"}
