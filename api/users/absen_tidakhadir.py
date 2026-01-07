import json
import os
import uuid
import aiomysql
from fastapi import APIRouter, Query, Request, HTTPException, Security, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from koneksi import get_db
from fastapi_jwt import JwtAuthorizationCredentials
from aiomysql import Error as aiomysqlerror
from jwt_auth import access_security
from api.admin.get_data import absensi_connection
from api.users.absensi import save_upload_file
from datetime import date, datetime, timedelta
from typing import Iterable, Dict, Any, Optional, Union

app = APIRouter(prefix="/absen_tidakhadir")

FOTO_TIDAK_HADIR = "api/images/tidak_hadir"
TIPE_CUTI = ("liburan", "cuti")
MEDIA_TYPE_PNG = "image/png"
IMAGE_EXTENSION_PNG = ".png"
STATUS_ERROR = "error"
STATUS_SUCCESS = "success"
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
EVENT_PENGAJUAN_CREATED = "pengajuan_created"
MESSAGE_TYPE_REQUIRED = "tipe_pengajuan wajib diisi"
MESSAGE_OVERRIDE_CONFIRM = (
  "Anda sudah melakukan absen hari ini, Anda Yakin ingin Mengoverride?"
)
MESSAGE_DB_ERROR_PREFIX = "Database Error"
MESSAGE_HTTP_ERROR_PREFIX = "HTTP Error Error"
MESSAGE_CONNECTION_ERROR_PREFIX = "Koneksi Error"
MESSAGE_REQUESTED = "Pengajuan di Minta"
MESSAGE_END_DATE_BEFORE_START = "Tanggal akhir tidak boleh sebelum tanggal mulai."
MESSAGE_VALID_NO_QUOTA = "Pengajuan valid (tidak membebani kuota tahun ini)."
MESSAGE_WITHIN_QUOTA = "Pengajuan masih dalam batas kuota."
MESSAGE_QUOTA_EXCEEDED = (
  "Pengajuan {requested} hari (di tahun ini) melebihi sisa kuota {remaining} hari."
)
DATE_FORMAT_YMD = "%Y-%m-%d"
RESPONSE_KEY_SUCCESS = "Sukses"
EMPTY_STRING = ""
DEFAULT_JATAH_CUTI = 12
WEEKDAY_SUNDAY_INDEX = 6
YEAR_START_MONTH = 1
YEAR_START_DAY = 1
YEAR_END_MONTH = 12
YEAR_END_DAY = 31
DAY_INCREMENT = 1
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_INTERNAL_SERVER_ERROR = 500
TIPE_CUTI_BERSAMA = "cuti_bersama"


@app.get("/foto_tidakhadir/{filename}")
def get_foto_tidakhadir(filename: str):
  img_path = os.path.join(FOTO_TIDAK_HADIR, filename)
  return FileResponse(img_path, media_type=MEDIA_TYPE_PNG)


@app.get("/")
async def get_data(
  month: Optional[str] = Query(None),
  year: Optional[str] = Query(None),
  user: JwtAuthorizationCredentials = Security(access_security),
):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          await cursor.execute(
            "SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;"
          )

          if not month and not year:
            q1 = "SELECT * FROM pengajuan_absen WHERE id_karyawan = %s"
            await cursor.execute(q1, user["id_karyawan"])

            # Return dalam bentuk dict
            items = await cursor.fetchall()
          else:
            q1 = "SELECT * FROM pengajuan_absen WHERE MONTH(tanggal_mulai) = %s and YEAR(tanggal_mulai) = %s and id_karyawan = %s"
            await cursor.execute(q1, (month, year, user["id_karyawan"]))

            # Return dalam bentuk dict
            items = await cursor.fetchall()

          return items
        except aiomysqlerror as e:
          return JSONResponse(
            content={
              "status": STATUS_ERROR,
              "message": f"{MESSAGE_DB_ERROR_PREFIX} {str(e)}",
            },
            status_code=HTTP_INTERNAL_SERVER_ERROR,
          )
        except HTTPException as e:
          return JSONResponse(
            content={
              "status": STATUS_ERROR,
              "message": f"{MESSAGE_HTTP_ERROR_PREFIX} {str(e)}",
            },
            status_code=e.status_code,
          )

  except Exception as e:
    return JSONResponse(
      content={
        "status": STATUS_ERROR,
        "message": f"{MESSAGE_CONNECTION_ERROR_PREFIX} {str(e)}",
      },
      status_code=HTTP_INTERNAL_SERVER_ERROR,
    )


@app.post("/store_data")
async def store_data(
  request: Request,
  background_tasks: BackgroundTasks,
  user: JwtAuthorizationCredentials = Security(access_security),
):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          await conn.begin()
          data = await request.form()

          # --- VALIDASI KOUTA CUTI ---
          # sesuaikan tipe yang dihitung sebagai cuti
          tipe_yang_dihitung_cuti = TIPE_CUTI

          # 2. Ambil tipe yang diajukan user dari payload
          tipe_diajukan_user = data.get("tipe_pengajuan")

          if not tipe_diajukan_user:
            await conn.rollback()
            return JSONResponse(
              content={"status": STATUS_ERROR, "message": MESSAGE_TYPE_REQUIRED},
              status_code=HTTP_BAD_REQUEST,
            )

          # 3. HANYA jalankan validasi JIKA tipe yang diajukan termasuk yang dihitung
          if tipe_diajukan_user in tipe_yang_dihitung_cuti:
            # 4. Panggil validasi. Perhatikan:
            #    Parameter 'tipe_dianggap_cuti' TETAP berisi SEMUA tipe yg dihitung,
            #    bukan hanya 'tipe_diajukan_user'.
            v = await validate_cuti_request(
              cursor,
              id_karyawan=user["id_karyawan"],
              tanggal_mulai=data["tanggal_mulai"],
              tanggal_akhir=data["tanggal_akhir"],
              tipe_dianggap_cuti=tipe_yang_dihitung_cuti,  # <-- Tetap pakai ini
              tahan_pending=True,
              lock_config=True,
            )

            if not v["ok"]:
              await conn.rollback()

              # (Saran: cleanup response error agar lebih rapi)
              detail_error = v.copy()
              detail_error.pop("ok", None)
              detail_error.pop("message", None)

              return JSONResponse(
                content={
                  "status": STATUS_ERROR,
                  "message": v["message"],
                  "detail": detail_error,
                },
                status_code=HTTP_BAD_REQUEST,
              )
          # --- END VALIDASI ---

          tanggal_mulai_str = data["tanggal_mulai"]
          tanggal_akhir_str = data["tanggal_akhir"]

          tanggal_mulai = datetime.strptime(tanggal_mulai_str, DATE_FORMAT_YMD).date()
          tanggal_akhir = datetime.strptime(tanggal_akhir_str, DATE_FORMAT_YMD).date()
          today = date.today()

          # Hanya perlu cek override kalau hari ini masuk dalam range pengajuan
          should_check_override = tanggal_mulai <= today <= tanggal_akhir

          rows_is_already_check_in = None
          if should_check_override:
            query_is_already_checkin = """
              SELECT * FROM absensi 
                WHERE 
                  id_karyawan = %s
                AND 
                  (tanggal_absen = CURDATE() or DATE(check_in) = CURDATE())
                LIMIT 1
            """
            await cursor.execute(query_is_already_checkin, (user["id_karyawan"],))
            rows_is_already_check_in = await cursor.fetchone()

          if rows_is_already_check_in:
            if "is_confirmed" in data and bool(data["is_confirmed"]) is True:
              query_override_status = """
                UPDATE absensi 
                  SET pengajuan = %s, status_absen = 'pending'
                WHERE 
                  id_absensi = %s
              """
              await cursor.execute(
                query_override_status,
                (data["tipe_pengajuan"], rows_is_already_check_in["id_absensi"]),
              )
            else:
              await conn.rollback()
              return JSONResponse(
                content={
                  "status": STATUS_ERROR,
                  "message": MESSAGE_OVERRIDE_CONFIRM,
                },
                status_code=HTTP_BAD_REQUEST,
              )

          # saveFile. cek key foto_lampiran ada atau nd
          if "foto_lampiran" in data:
            filename = f"{uuid.uuid4()}{IMAGE_EXTENSION_PNG}"
            file_location = os.path.join(FOTO_TIDAK_HADIR, filename)

            # content = await data['foto_lampiran'].read()
            # with open(file_location, "wb") as f:
            #   f.write(content)
            background_tasks.add_task(
              save_upload_file, data["foto_lampiran"], file_location
            )

          q1 = """
            -- set unique key di id_karyawan & tanggal_mulai biar bs upsert
            INSERT INTO pengajuan_absen(
              id_karyawan, tipe_pengajuan, tanggal_mulai, tanggal_akhir, 
              foto_lampiran, keterangan
            )
            VALUES(%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              tipe_pengajuan = VALUES(tipe_pengajuan),
              tanggal_akhir = VALUES(tanggal_akhir),
              foto_lampiran = VALUES(foto_lampiran),
              keterangan = VALUES(keterangan),
              status = 'pending',
              alasan_penolakan = NULL
          """
          q1_values = (
            user["id_karyawan"],
            data["tipe_pengajuan"],
            data["tanggal_mulai"],
            data["tanggal_akhir"],
            filename if "foto_lampiran" in data else EMPTY_STRING,
            data["keterangan"],
          )
          await cursor.execute(q1, q1_values)
          await conn.commit()

          await broadcast_pengajuan_created(
            {
              "id_pengajuan": cursor.lastrowid,
              "id_karyawan": user["id_karyawan"],
              "tipe_pengajuan": data["tipe_pengajuan"],
              "tanggal_mulai": data["tanggal_mulai"],
              "tanggal_akhir": data["tanggal_akhir"],
              "foto_lampiran": filename if "foto_lampiran" in data else EMPTY_STRING,
              "keterangan": data["keterangan"],
            },
            pool,
          )

          return {RESPONSE_KEY_SUCCESS: MESSAGE_REQUESTED}

        except aiomysqlerror as e:
          await conn.rollback()
          print(MESSAGE_DB_ERROR_PREFIX, str(e))
          return JSONResponse(
            content={
              "status": STATUS_ERROR,
              "message": f"{MESSAGE_DB_ERROR_PREFIX} {str(e)}",
            },
            status_code=HTTP_INTERNAL_SERVER_ERROR,
          )
        except HTTPException as e:
          await conn.rollback()
          print(MESSAGE_HTTP_ERROR_PREFIX, str(e))
          return JSONResponse(
            content={
              "status": STATUS_ERROR,
              "message": f"{MESSAGE_HTTP_ERROR_PREFIX} {str(e)}",
            },
            status_code=e.status_code,
          )

  except Exception as e:
    print(MESSAGE_CONNECTION_ERROR_PREFIX, str(e))
    return JSONResponse(
      content={
        "status": STATUS_ERROR,
        "message": f"{MESSAGE_CONNECTION_ERROR_PREFIX} {str(e)}",
      },
      status_code=HTTP_INTERNAL_SERVER_ERROR,
    )


def _as_date(v: str) -> date:
  # terima 'YYYY-MM-DD' atau datetime
  if isinstance(v, date):
    return v
  if isinstance(v, datetime):
    return v.date()
  return datetime.strptime(v, DATE_FORMAT_YMD).date()


@app.get("/summary_cuti")
async def get_summary_cuti_saya(
  user: JwtAuthorizationCredentials = Security(access_security),
):
  """
  Endpoint untuk mengecek ringkasan (summary) cuti
  milik user yang sedang login.
  """
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          # Tentukan tipe apa saja yang dihitung sebagai cuti
          # (Harus sama dengan yang di 'store_data')
          tipe_cuti = TIPE_CUTI

          # Panggil fungsi summary yang sudah ada
          summary = await get_cuti_summary(
            cursor,
            id_karyawan=user["id_karyawan"],
            tipe_dianggap_cuti=tipe_cuti,
            tahan_pending=True,  # Tampilkan sisa RIL (termasuk pending)
            lock_config=False,  # PENTING: 'False' saat hanya GET/baca data
          )

          # Kembalikan data summary sebagai JSON
          return JSONResponse(
            content={"status": STATUS_SUCCESS, "data": summary}, status_code=HTTP_OK
          )

        except aiomysqlerror as e:
          return JSONResponse(
            content={
              "status": STATUS_ERROR,
              "message": f"{MESSAGE_DB_ERROR_PREFIX} {str(e)}",
            },
            status_code=HTTP_INTERNAL_SERVER_ERROR,
          )
        except HTTPException as e:
          return JSONResponse(
            content={
              "status": STATUS_ERROR,
              "message": f"{MESSAGE_HTTP_ERROR_PREFIX} {str(e)}",
            },
            status_code=e.status_code,
          )

  except Exception as e:
    return JSONResponse(
      content={
        "status": STATUS_ERROR,
        "message": f"{MESSAGE_CONNECTION_ERROR_PREFIX} {str(e)}",
      },
      status_code=HTTP_INTERNAL_SERVER_ERROR,
    )


# Tambahkan parameter holidays
def calculate_working_days(
  start_date: date, end_date: date, holidays: Dict[date, str]
) -> int:
  """
  Menghitung durasi cuti PRIBADI.
  Mengabaikan Weekend, Libur Nasional, DAN Cuti Bersama.
  (Karena Cuti Bersama dipotong dari 'Plafon' kuota, bukan dari durasi request).
  """
  total_days = 0
  current_date = start_date
  while current_date <= end_date:
    # 1. Cek Weekend (0-4 = Senin-Jumat, 5=Sabtu, 6=Minggu)
    if current_date.weekday() < WEEKDAY_SUNDAY_INDEX:
      # 2. Cek apakah tanggal ini ada di tabel hari_libur?
      #    Baik itu 'nasional' atau 'cuti_bersama', JANGAN dihitung sebagai
      #    hari pengajuan cuti pribadi.
      if current_date not in holidays:
        total_days += 1

    current_date += timedelta(days=DAY_INCREMENT)
  return total_days


async def get_cuti_summary(
  cursor: aiomysql.DictCursor,
  id_karyawan: str,
  tipe_dianggap_cuti: Iterable[str] = TIPE_CUTI,
  tahan_pending: bool = True,
  lock_config: bool = False,
) -> Dict[str, Any]:
  """
  Mengembalikan ringkasan cuti tahun berjalan.
  Fitur:
  - 6 Hari Kerja (Senin-Sabtu).
  - Jatah cuti per individu (dari tabel karyawan).
  - Cuti Bersama otomatis memotong jatah (jika jatuh Senin-Sabtu).
  """
  # 1. Tentukan rentang tahun berjalan
  tahun_ini = date.today().year
  start_tahun_ini = date(tahun_ini, YEAR_START_MONTH, YEAR_START_DAY)
  end_tahun_ini = date(tahun_ini, YEAR_END_MONTH, YEAR_END_DAY)

  # 2. AMBIL KUOTA AWAL DARI TABEL KARYAWAN
  #    (Default 12 jika belum di-set)
  sql_karyawan = "SELECT jatah_cuti_tahunan FROM karyawan WHERE id_karyawan = %s"
  await cursor.execute(sql_karyawan, (id_karyawan,))
  row_kry = await cursor.fetchone()
  jatah_awal = (row_kry or {}).get("jatah_cuti_tahunan", DEFAULT_JATAH_CUTI)

  # 3. AMBIL DATA HARI LIBUR & HITUNG POTONGAN CUTI BERSAMA
  #    Kita load semua libur tahun ini ke dictionary memori
  sql_libur = "SELECT tanggal, tipe FROM hari_libur WHERE YEAR(tanggal) = %s"
  await cursor.execute(sql_libur, (tahun_ini,))
  rows_libur = await cursor.fetchall()

  holidays_dict = {}
  total_potongan_bersama = 0

  for row in rows_libur:
    tgl = _as_date(row["tanggal"])
    tipe = row["tipe"]
    holidays_dict[tgl] = tipe

    # LOGIKA POTONGAN JATAH:
    # Jika tipe 'cuti_bersama' jatuh di hari kerja (Senin-Sabtu),
    # maka jatah cuti karyawan dikurangi.
    if tipe == TIPE_CUTI_BERSAMA:
      if tgl.weekday() < WEEKDAY_SUNDAY_INDEX:
        total_potongan_bersama += 1

  # 4. HITUNG KUOTA EFEKTIF
  #    Kuota yang bisa dipakai = Jatah Awal - Cuti Bersama
  kuota_efektif = max(0, jatah_awal - total_potongan_bersama)

  # 5. AMBIL PENGAJUAN PRIBADI USER
  tipe_list = list(tipe_dianggap_cuti)

  # Jika tidak ada tipe cuti yang didefinisikan, return data dasar
  if not tipe_list:
    return {
      "jatah_awal": jatah_awal,
      "potongan_cuti_bersama": total_potongan_bersama,
      "kuota_efektif": kuota_efektif,
      "hari_approved": 0,
      "hari_pending": 0,
      "sisa_tanpa_pending": kuota_efektif,
      "sisa_dengan_pending": kuota_efektif,
    }

  in_clause_tipe = ",".join(["%s"] * len(tipe_list))
  sql_fetch = f"""
    SELECT status, tanggal_mulai, tanggal_akhir
    FROM pengajuan_absen
    WHERE id_karyawan = %s
    AND status IN ('approved', 'pending')
    AND tipe_pengajuan IN ({in_clause_tipe})
    AND tanggal_mulai <= %s AND tanggal_akhir >= %s
  """
  params = (id_karyawan, *tipe_list, end_tahun_ini, start_tahun_ini)
  await cursor.execute(sql_fetch, params)
  semua_pengajuan = await cursor.fetchall()

  # 6. HITUNG DURASI PEMAKAIAN
  hari_approved = 0
  hari_pending = 0

  for pengajuan in semua_pengajuan:
    p_start = _as_date(pengajuan["tanggal_mulai"])
    p_end = _as_date(pengajuan["tanggal_akhir"])

    # Cari irisan (overlap) dengan tahun ini
    overlap_start = max(p_start, start_tahun_ini)
    overlap_end = min(p_end, end_tahun_ini)

    if overlap_end >= overlap_start:
      # Hitung hari kerja (Senin-Sabtu) exclude Libur & Cuti Bersama
      durasi = calculate_working_days(overlap_start, overlap_end, holidays_dict)

      if durasi > 0:
        if pengajuan["status"] == STATUS_APPROVED:
          hari_approved += durasi
        elif pengajuan["status"] == STATUS_PENDING:
          hari_pending += durasi

  # 7. HITUNG SISA AKHIR
  total_terpakai_pribadi = hari_approved
  if tahan_pending:
    total_terpakai_pribadi += hari_pending

  sisa_dengan_pending = max(0, kuota_efektif - total_terpakai_pribadi)
  sisa_tanpa_pending = max(0, kuota_efektif - hari_approved)

  return {
    "jatah_awal": jatah_awal,  # Cth: 12
    "potongan_cuti_bersama": total_potongan_bersama,  # Cth: 4 (Jatuh di Weekday)
    "kuota_efektif": kuota_efektif,  # Cth: 8 (12-4)
    "hari_approved": hari_approved,  # Cuti pribadi yg sudah di-acc
    "hari_pending": hari_pending,  # Cuti pribadi yg msh pending
    "sisa_tanpa_pending": sisa_tanpa_pending,  # Sisa jika pending ditolak
    "sisa_dengan_pending": sisa_dengan_pending,  # Sisa real saat ini (aman untuk validasi)
  }


async def validate_cuti_request(
  cursor: aiomysql.DictCursor,
  id_karyawan: str,
  tanggal_mulai: Union[str, date],
  tanggal_akhir: Union[str, date],
  tipe_dianggap_cuti: Iterable[str] = TIPE_CUTI,
  tahan_pending: bool = True,
  lock_config: bool = True,
) -> Dict[str, Any]:
  """
  Validasi pengajuan cuti baru terhadap sisa kuota.
  Fungsi ini tidak berubah, tapi sekarang memanggil get_cuti_summary versi baru.
  """
  t_mulai = _as_date(tanggal_mulai)
  t_akhir = _as_date(tanggal_akhir)

  if t_akhir < t_mulai:
    return {
      "ok": False,
      "message": MESSAGE_END_DATE_BEFORE_START,
      "hari_diajukan": 0,
    }

  # Hitung HANYA hari yang ada di TAHUN INI
  # (Jika pengajuan lintas tahun, misal 29 Des 2025 - 5 Jan 2026,
  #  kita hanya validasi yang 3 hari di 2025)
  tahun_ini = date.today().year
  start_tahun_ini = date(tahun_ini, YEAR_START_MONTH, YEAR_START_DAY)
  end_tahun_ini = date(tahun_ini, YEAR_END_MONTH, YEAR_END_DAY)

  # Cek apakah pengajuan ini relevan untuk tahun ini
  if t_mulai > end_tahun_ini or t_akhir < start_tahun_ini:
    # Pengajuan ini sepenuhnya di luar tahun berjalan (misal cuti untuk Januari 2026)
    # Anda bisa tambahkan logika validasi untuk tahun depan jika perlu
    # Untuk saat ini, kita anggap valid (0 hari membebani tahun ini)
    hari_diajukan_tahun_ini = 0
  else:
    # Jika tumpang tindih, hitung hari yang masuk tahun ini
    overlap_start = max(t_mulai, start_tahun_ini)
    overlap_end = min(t_akhir, end_tahun_ini)

    if overlap_end >= overlap_start:
      # --- PERBAIKAN: Ambil data libur dulu ---
      sql_libur = "SELECT tanggal, tipe FROM hari_libur WHERE YEAR(tanggal) = %s"
      await cursor.execute(sql_libur, (tahun_ini,))
      rows_libur = await cursor.fetchall()

      # Konversi ke Dictionary
      holidays_dict = {_as_date(row["tanggal"]): row["tipe"] for row in rows_libur}

      # Masukkan holidays_dict ke dalam fungsi
      hari_diajukan_tahun_ini = calculate_working_days(
        overlap_start, overlap_end, holidays_dict
      )
    else:
      hari_diajukan_tahun_ini = 0

  if hari_diajukan_tahun_ini <= 0:
    # Tidak ada hari yang membebani tahun ini
    return {
      "ok": True,
      "message": MESSAGE_VALID_NO_QUOTA,
      "hari_diajukan": 0,  # Total hari yang diajukan mungkin > 0, tapi 0 utk tahun ini
    }

  # Panggil fungsi summary versi baru
  ringkasan = await get_cuti_summary(
    cursor,
    id_karyawan=id_karyawan,
    tipe_dianggap_cuti=tipe_dianggap_cuti,
    tahan_pending=tahan_pending,
    lock_config=lock_config,  # Penting untuk meneruskan lock
  )

  sisa_kuota = (
    ringkasan["sisa_dengan_pending"]
    if tahan_pending
    else ringkasan["sisa_tanpa_pending"]
  )

  if hari_diajukan_tahun_ini > sisa_kuota:
    return {
      "ok": False,
      "message": MESSAGE_QUOTA_EXCEEDED.format(
        requested=hari_diajukan_tahun_ini,
        remaining=sisa_kuota,
      ),
      "hari_diajukan": hari_diajukan_tahun_ini,
      **ringkasan,
    }

  return {
    "ok": True,
    "message": MESSAGE_WITHIN_QUOTA,
    "hari_diajukan": hari_diajukan_tahun_ini,
    **ringkasan,
  }


async def broadcast_pengajuan_created(pa_row: dict, pool: aiomysql.Pool):
  # effective_date = str(pa_row["tanggal_mulai"])  # "YYYY-MM-DD"
  data_karyawan = {}

  async with pool.acquire() as conn:
    async with conn.cursor(aiomysql.DictCursor) as cursor:
      await cursor.execute(
        "SELECT * FROM karyawan WHERE id_karyawan = %s", (pa_row["id_karyawan"],)
      )
      data_karyawan = await cursor.fetchone()

  msg = {
    "event": EVENT_PENGAJUAN_CREATED,
    "message": f"{data_karyawan['nama_karyawan']} membuat pengajuan {pa_row['tipe_pengajuan']}",
    "effective_date": str(pa_row["tanggal_mulai"]),  # <-- kunci
    "payload": {
      "id_pengajuan": pa_row["id_pengajuan"],
      "nama_karyawan": data_karyawan["nama_karyawan"],
      "tipe_pengajuan": pa_row["tipe_pengajuan"],
      "tanggal_mulai": str(pa_row["tanggal_mulai"]),
      "tanggal_akhir": str(pa_row["tanggal_akhir"]),
      "lampiran": pa_row.get("lampiran", EMPTY_STRING) or EMPTY_STRING,
      "keterangan": pa_row.get("keterangan", EMPTY_STRING) or EMPTY_STRING,
      "status": STATUS_PENDING,
    },
  }

  dead = []
  for ws in absensi_connection:
    try:
      await ws.send_text(json.dumps(msg))
    except Exception:
      dead.append(ws)
  for ws in dead:
    absensi_connection.remove(ws)


