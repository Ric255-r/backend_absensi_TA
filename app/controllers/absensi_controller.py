import json
import os
import shutil
import uuid
from datetime import datetime, timedelta, time

from fastapi import BackgroundTasks, HTTPException, UploadFile
from fastapi_jwt import JwtAuthorizationCredentials
from tortoise import Tortoise
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.core.serializer import serialize_data
from app.models import Absensi, JadwalKerja, Karyawan, KonfigurasiAplikasi
from app.models.pengajuan_absen import PengajuanAbsen
from app.realtime.absensi_ws import absensi_connections
from app.schemas.requests.absensi import CheckInRequest, CheckOutRequest
from utils.fn_log_users import logger as logger_user

FOTO_CHECKIN = "api_legacy/images/foto_checkin"
FOTO_CHECKOUT = "api_legacy/images/foto_checkout"
STATUS_OK = "ok"
MESSAGE_ALREADY_CHECKIN = "Anda Sudah Checkin"
MESSAGE_ALREADY_CHECKOUT = "Anda Sudah CheckOut"
MESSAGE_NO_CHECKIN = "Belum Ada Checkin"
MESSAGE_NO_CHECKOUT = "Belum Ada Checkout"


def _day_bounds(dt: datetime) -> tuple[datetime, datetime]:
  start = datetime.combine(dt.date(), time.min)
  end = start + timedelta(days=1)
  return start, end


def _normalize_db_time(value) -> time:
  if isinstance(value, time):
    return value

  if isinstance(value, timedelta):
    total_seconds = int(value.total_seconds()) % (24 * 3600)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return time(hour=hours, minute=minutes, second=seconds)

  if isinstance(value, str):
    return time.fromisoformat(value)

  raise HTTPException(status_code=500, detail="Format waktu database tidak valid")


def _day_to_indo(day_name_en: str) -> str:
  mapping = {
    "Monday": "Senin",
    "Tuesday": "Selasa",
    "Wednesday": "Rabu",
    "Thursday": "Kamis",
    "Friday": "Jumat",
    "Saturday": "Sabtu",
    "Sunday": "Minggu",
  }
  return mapping.get(day_name_en, "Minggu")


def save_upload_file(upload: UploadFile, dest: str) -> None:
  with open(dest, "wb") as f:
    shutil.copyfileobj(upload.file, f)  # stream, no read() besar ke memori


async def get_attendance_data(
  user: JwtAuthorizationCredentials,
  month: str | None = None,
  year: str | None = None,
):
  logger_user.info(f"Karyawan: {user['nama_karyawan']} Mengakses Data Absensi")

  # Legacy behavior: tanpa month & year -> kembalikan 1 data absensi hari ini (dict)
  if not month and not year:
    day_start, day_end = _day_bounds(datetime.now())
    items = await Absensi.filter(
      karyawan_id=user["id_karyawan"],
      tanggal_absen__gte=day_start,
      tanggal_absen__lt=day_end,
    ).limit(1).values()
    item = items[0] if items else None
    return item

  # Legacy SQL butuh month + year; jika salah satu tidak ada, hasil effectively kosong.
  if not month or not year:
    return []

  absensi_records = await Absensi.filter(
    tanggal_absen__month=int(month),
    tanggal_absen__year=int(year),
    karyawan_id=user["id_karyawan"],
  ).values().order_by("tanggal_absen")

  report_data: list[dict] = []

  # Legacy behavior: LEFT JOIN pengajuan_absen berdasarkan rentang tanggal,
  # tanpa filter status pengajuan.
  for absensi in absensi_records:
    tgl_absen = absensi["tanggal_absen"].date()

    pengajuan_match = await PengajuanAbsen.filter(
      karyawan_id=user["id_karyawan"],
      tanggal_mulai__lte=tgl_absen,
      tanggal_akhir__gte=tgl_absen,
    ).limit(1).values("keterangan", "foto_lampiran")
    pengajuan_match = pengajuan_match[0] if pengajuan_match else None

    row = dict(absensi)
    row["keterangan"] = pengajuan_match["keterangan"] if pengajuan_match else None
    row["foto_lampiran"] = (
      pengajuan_match["foto_lampiran"] if pengajuan_match else None
    )
    report_data.append(row)

  return report_data


async def validate_check_in_attendance(
  user: JwtAuthorizationCredentials,
) -> dict:
  now = datetime.now()
  day_start, day_end = _day_bounds(now)
  has_checkin = await Absensi.filter(
    karyawan_id=user["id_karyawan"],
    tanggal_absen__gte=day_start,
    tanggal_absen__lt=day_end,
    check_in__isnull=False,
  ).exists()

  in_pengajuan = await PengajuanAbsen.filter(
    Q(karyawan_id=user["id_karyawan"])
    & Q(tanggal_mulai__lte=now.date())
    & Q(tanggal_akhir__gte=now.date())
    & Q(status="approved")
  ).exists()

  if bool(has_checkin) or bool(in_pengajuan):
    raise HTTPException(
      status_code=403,
      detail=MESSAGE_ALREADY_CHECKIN,
    )

  return {"status": STATUS_OK, "message": MESSAGE_NO_CHECKIN}


async def validate_check_out_attendance(
  user: JwtAuthorizationCredentials,
) -> dict:
  now = datetime.now()
  day_start, day_end = _day_bounds(now)
  has_check_out = await Absensi.filter(
    karyawan_id=user["id_karyawan"],
    tanggal_absen__gte=day_start,
    tanggal_absen__lt=day_end,
    check_out__isnull=False,
  ).exists()

  has_pengajuan = await PengajuanAbsen.filter(
    Q(karyawan_id=user["id_karyawan"])
    & Q(tanggal_mulai__lte=now.date())
    & Q(tanggal_akhir__gte=now.date())
    & Q(status="approved")
  ).exists()

  if bool(has_check_out) or bool(has_pengajuan):
    raise HTTPException(
      status_code=403,
      detail=MESSAGE_ALREADY_CHECKOUT,
    )

  return {"status": STATUS_OK, "message": MESSAGE_NO_CHECKOUT}


async def _get_db_day_and_time() -> tuple[str, time]:
  conn = Tortoise.get_connection("default")
  await conn.execute_query("SET @@lc_time_names = 'id_ID';")

  day_rows = await conn.execute_query_dict("SELECT DAYNAME(DATE(NOW())) AS hari_ini;")
  if not day_rows:
    raise HTTPException(status_code=500, detail="Gagal mengambil hari dari database")

  time_rows = await conn.execute_query_dict("SELECT TIME(NOW()) AS jam_skrg;")
  if not time_rows:
    raise HTTPException(status_code=500, detail="Gagal mengambil waktu dari database")

  return day_rows[0]["hari_ini"], _normalize_db_time(time_rows[0]["jam_skrg"])


async def store_check_in_attendance(
  payload: CheckInRequest,
  photo: UploadFile,
  background_task: BackgroundTasks,
  user: JwtAuthorizationCredentials,
) -> dict:
  now = datetime.now()
  day_start, day_end = _day_bounds(now)
  day_name_indo, db_now_time = await _get_db_day_and_time()

  config_rows = await KonfigurasiAplikasi.all().order_by("id_pengaturan").limit(1)
  config = config_rows[0] if config_rows else None
  if not config:
    raise HTTPException(status_code=500, detail="Konfigurasi aplikasi tidak ditemukan")

  schedule_rows = await JadwalKerja.filter(hari_dalam_seminggu=day_name_indo).limit(1)
  schedule = schedule_rows[0] if schedule_rows else None
  if not schedule or not schedule.shift_mulai:
    raise HTTPException(
      status_code=404,
      detail=f"Jadwal kerja untuk hari {day_name_indo} tidak ditemukan",
    )

  # MySQL TIME dapat terbaca sebagai timedelta; normalisasi dulu ke datetime.time.
  shift_mulai_time = _normalize_db_time(schedule.shift_mulai)
  batas_waktu_checkin = datetime.combine(now.date(), shift_mulai_time) + timedelta(
    minutes=config.toleransi_terlambat
  )
  waktu_checkin_sekarang = datetime.combine(now.date(), db_now_time)
  is_telat = 1 if waktu_checkin_sekarang > batas_waktu_checkin else 0

  filename = f"{uuid.uuid4()}.jpg"
  file_location = os.path.join(FOTO_CHECKIN, filename)
  os.makedirs(FOTO_CHECKIN, exist_ok=True)

  async with in_transaction() as db:
    await Absensi.create(
      karyawan_id=user["id_karyawan"],
      tanggal_absen=now,
      check_in=now,
      latitude_checkin=payload.latitude_checkin,
      longitude_checkin=payload.longitude_checkin,
      foto_checkin=filename,
      is_telat=is_telat,
      pengajuan=payload.pengajuan or "hadir",
      using_db=db,
    )

  data_karyawan_rows = await Karyawan.filter(id_karyawan=user["id_karyawan"]).limit(1).values(
    "id_karyawan", "nama_karyawan"
  )
  data_karyawan = data_karyawan_rows[0] if data_karyawan_rows else None

  if data_karyawan:
    for ws_con in absensi_connections:
      try:
        await ws_con.send_text(
          json.dumps(
            {
              "message": f"Check in baru dari {data_karyawan['nama_karyawan']}",
              "data": serialize_data(data_karyawan),
            }
          )
        )
      except Exception:
        pass

  background_task.add_task(save_upload_file, photo, file_location)
  logger_user.info(f"Karyawan: {user['nama_karyawan']} Mengajukan Presensi Check In")

  return {"status": STATUS_OK, "message": "Sukses Simpan Data"}


async def store_check_out_attendance(
  payload: CheckOutRequest,
  photo: UploadFile,
  background_task: BackgroundTasks,
  user: JwtAuthorizationCredentials,
) -> dict:
  now = datetime.now()
  day_start, day_end = _day_bounds(now)

  filename = f"{uuid.uuid4()}.jpg"
  file_location = os.path.join(FOTO_CHECKOUT, filename)
  os.makedirs(FOTO_CHECKOUT, exist_ok=True)

  async with in_transaction() as db:
    await Absensi.filter(
      tanggal_absen__gte=day_start,
      tanggal_absen__lt=day_end,
      karyawan_id=user["id_karyawan"],
    ).using_db(db).update(
      check_out=now,
      latitude_checkout=payload.latitude_checkout,
      longitude_checkout=payload.longitude_checkout,
      foto_checkout=filename,
    )

  data_karyawan_rows = await Karyawan.filter(id_karyawan=user["id_karyawan"]).limit(1).values(
    "id_karyawan", "nama_karyawan"
  )
  data_karyawan = data_karyawan_rows[0] if data_karyawan_rows else None

  if data_karyawan:
    for ws_con in absensi_connections:
      try:
        await ws_con.send_text(
          json.dumps(
            {
              "message": f"Absen checkout baru dari {data_karyawan['nama_karyawan']}",
              "data": serialize_data(data_karyawan),
            }
          )
        )
      except Exception:
        pass

  background_task.add_task(save_upload_file, photo, file_location)
  logger_user.info(f"Karyawan: {user['nama_karyawan']} Mengajukan Presensi Check Out")

  return {"status": STATUS_OK, "message": "Sukses Update Data Absensi"}
