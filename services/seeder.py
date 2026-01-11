import asyncio
from datetime import timedelta
import aiomysql
from fastapi import APIRouter, HTTPException
import pandas as pd
from api.users.absensi import _get_lateness_tolerance
from koneksi import get_db
from aiomysql import Error as aiomysqlerror
import random

app = APIRouter(prefix="/seed")


# --- 1. Helper: Ambil Jadwal dengan Key (Hari, Shift) ---
async def _get_schedule_map(pool: aiomysql.Pool):
  """
  Mengambil jadwal kerja.
  Return Dictionary dengan Key Tuple: (hari, nama_shift) -> value: shift_mulai
  Contoh: {('Senin', 'pagi'): 08:00:00, ('Senin', 'sore'): 13:00:00}
  """
  schedule_map = {}
  async with pool.acquire() as conn:
    async with conn.cursor(aiomysql.DictCursor) as cursor:
      # Mengambil kolom nama_shift juga
      await cursor.execute(
        "SELECT hari_dalam_seminggu, nama_shift, shift_mulai FROM jadwal_kerja"
      )
      rows = await cursor.fetchall()
      for row in rows:
        # Key-nya adalah Tuple (Hari, Shift)
        key = (row["hari_dalam_seminggu"], row["nama_shift"])
        schedule_map[key] = row["shift_mulai"]
  return schedule_map


# --- 2. Helper: Ambil Data Karyawan & Shift Mereka ---
async def _get_employees_with_shift(pool: aiomysql.Pool):
  """
  Mengambil list karyawan beserta shift yang assign ke mereka.
  """
  employees = []
  async with pool.acquire() as conn:
    async with conn.cursor(aiomysql.DictCursor) as cursor:
      # Ambil id dan kode_shift
      await cursor.execute(
        "SELECT id_karyawan, kode_shift FROM karyawan WHERE status = 'aktif'"
      )
      rows = await cursor.fetchall()
      for row in rows:
        # Kita assign foto dummy random atau berdasarkan ID
        employees.append(
          {
            "id": row["id_karyawan"],
            "shift": row["kode_shift"],
            "foto": f"dummy_{row['id_karyawan']}.jpg",
          }
        )
  return employees


# --- 3. Main Function ---
@app.post("/generate_dummy_attendance")
async def generate_dummy_attendance():
  try:
    pool = await get_db()

    # Eksekusi parallel untuk mempercepat
    config_task = _get_lateness_tolerance(pool)
    schedule_task = _get_schedule_map(pool)
    employees_task = _get_employees_with_shift(pool)

    config, schedule_map, employees = await asyncio.gather(
      config_task, schedule_task, employees_task
    )

    if not config:
      raise HTTPException(status_code=500, detail="Config Kosong")
    if not schedule_map:
      raise HTTPException(status_code=500, detail="Jadwal Kosong")
    if not employees:
      raise HTTPException(status_code=500, detail="Data Karyawan Kosong")

    lateness_tolerance_minutes = config["toleransi_terlambat"]

  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

  # Mapping Hari Pandas (Inggris) -> DB (Indo)
  day_translation = {
    "Monday": "Senin",
    "Tuesday": "Selasa",
    "Wednesday": "Rabu",
    "Thursday": "Kamis",
    "Friday": "Jumat",
    "Saturday": "Sabtu",
    "Sunday": "Minggu",
  }

  # Range Tanggal
  start_date = pd.Timestamp("2025-12-01")
  end_date = pd.Timestamp("2025-12-31")
  date_range = pd.date_range(start_date, end_date)

  attendance_data = []

  employee_attendance_data = [
    ("K001", "foto1.jpg"),
    ("K002", "foto2.jpg"),
    ("K003", "foto3.jpg"),
    ("K004", "foto4.jpg"),
    ("K005", "foto5.jpg"),
    ("K006", "foto6.jpg"),
    ("K007", "foto7.jpg"),
    ("K008", "foto8.jpg"),
    ("K009", "foto9.jpg"),
    ("K010", "foto10.jpg"),
    ("K011", "foto11.jpg"),
    ("K012", "foto12.jpg"),
    ("K013", "foto13.jpg"),
    ("K014", "foto14.jpg"),
    ("K015", "foto15.jpg"),
  ]
  foto_by_emp_id = dict(employee_attendance_data)

  for date_obj in date_range:
    english_day = date_obj.day_name()
    indo_day = day_translation.get(english_day)

    date_str = date_obj.strftime("%Y-%m-%d")

    # Loop per Karyawan
    for emp in employees:
      emp_id = emp["id"]
      emp_shift = emp["shift"]  # 'pagi' atau 'sore'
      foto = foto_by_emp_id.get(emp_id, emp["foto"])

      # Cari Jadwal spesifik untuk (Hari Ini + Shift Karyawan Ini)
      schedule_key = (indo_day, emp_shift)

      # Jika tidak ada jadwal (misal Minggu atau shift pagi libur di hari Jumat), skip
      if schedule_key not in schedule_map:
        continue

      # Jam mulai shift (timedelta)
      shift_start_delta = schedule_map[schedule_key]

      # Waktu dasar masuk (Misal: 08:00 atau 13:00)
      base_shift_time = date_obj + shift_start_delta

      # Batas toleransi untuk penentuan status telat
      deadline_time = base_shift_time + timedelta(minutes=lateness_tolerance_minutes)

      # --- LOGIC RANDOMIZATION (REQUEST ANDA) ---
      # "Start dari jam kerja... ditambah random maksimal 1 jam"
      # Artinya range: 0 menit s/d 60 menit dari jam masuk.

      random_delay_minutes = random.randint(0, 60)
      random_seconds = random.randint(0, 59)

      # Waktu Check-in Aktual
      actual_checkin_dt = base_shift_time + timedelta(
        minutes=random_delay_minutes, seconds=random_seconds
      )
      time_attend_str = actual_checkin_dt.strftime("%H:%M:%S")

      # --- LOGIC PENENTUAN STATUS TELAT ---
      # Bandingkan Checkin Aktual dengan Deadline (Jam Masuk + Toleransi)
      if actual_checkin_dt > deadline_time:
        is_late = 1
      else:
        is_late = 0

      # Checkout (9 jam setelah checkin agar realistis)
      actual_checkout_dt = actual_checkin_dt + timedelta(hours=9)
      time_checkout_str = actual_checkout_dt.strftime("%H:%M:%S")

      attendance_data.append(
        (
          emp_id,
          f"{date_str} {time_attend_str}",  # tanggal_absen
          f"{date_str} {time_attend_str}",  # check_in
          f"{date_str} {time_checkout_str}",  # check_out
          -0.03020289202263597,  # latitude_checkin
          109.3217448800716,  # longitude_checkin
          -0.03020289202263597,  # latitude_checkout
          109.3217448800716,  # longitude_checkout
          foto,  # foto_checkin
          foto,  # foto_checkout
          "hadir",  # pengajuan
          is_late,  # is_telat
          "approved",  # status_absen
          None,  # alasan_penolakan
        )
      )

  # Insert Bulk
  try:
    if attendance_data:
      result = await insert_bulk_attendance(
        attendance_data
      )  # Pastikan fungsi ini ada/diimport
      if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
      return result
    else:
      return {
        "status": "ok",
        "message": "Tidak ada data yang digenerate (Mungkin hari libur semua?)",
      }

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


async def insert_bulk_attendance(attendance_data: list):
  """
  Helper function to insert bulk attendance data
  :param attendance_data: List of tuples containing attendance data
  :return: Dictionary with status and message
  """
  try:
    pool = await get_db()
    batch_size = 50  # Process 50 records at a time
    total_records = len(attendance_data)
    inserted_count = 0

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          await conn.begin()

          # Prepare the base query
          base_query = """
            INSERT INTO `absensi` (
                `id_karyawan`, `tanggal_absen`, `check_in`, `check_out`, 
                `latitude_checkin`, `longitude_checkin`, `latitude_checkout`, `longitude_checkout`, 
                `foto_checkin`, `foto_checkout`, `pengajuan`, `is_telat`, `status_absen`, `alasan_penolakan`
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
          """

          # Process in batches
          for i in range(0, total_records, batch_size):
            batch = attendance_data[i : i + batch_size]
            await cursor.executemany(base_query, batch)
            inserted_count += len(batch)

          await conn.commit()
          return {
            "status": "ok",
            "message": f"Successfully inserted {inserted_count} attendance records",
            "inserted_count": inserted_count,
          }

        except aiomysqlerror as e:
          await conn.rollback()
          return {
            "status": "error",
            "message": f"Database Error: {str(e)}",
            "inserted_count": inserted_count,
          }

  except Exception as e:
    return {
      "status": "error",
      "message": f"Connection Error: {str(e)}",
      "inserted_count": 0,
    }


async def insert_bulk_employees(employee_data: list):
  """
  Helper function to insert bulk employee data
  :param employee_data: List of tuples containing employee data
  :return: Dictionary with status and message
  """
  try:
    pool = await get_db()
    total_records = len(employee_data)
    inserted_count = 0

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          await conn.begin()

          # Prepare the base query
          base_query = """
              INSERT INTO `karyawan` (
                  `id_karyawan`, `nama_karyawan`, `email_karyawan`, `nomor_hp`, 
                  `foto_profile`, `tanggal_rekrut`, `status`, `id_departemen`, `posisi`
              ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
          """

          # Insert all records at once
          await cursor.executemany(base_query, employee_data)
          inserted_count = total_records

          await conn.commit()
          return {
            "status": "ok",
            "message": f"Successfully inserted {inserted_count} employee records",
            "inserted_count": inserted_count,
          }

        except aiomysql.Error as e:
          await conn.rollback()
          return {
            "status": "error",
            "message": f"Database Error: {str(e)}",
            "inserted_count": inserted_count,
          }

  except Exception as e:
    return {
      "status": "error",
      "message": f"Connection Error: {str(e)}",
      "inserted_count": 0,
    }


@app.post("/generate_dummy_employees")
async def generate_dummy_employees():
  # List of employees with their data
  employees = [
    (1, "marifal safarido"),
    (2, "habta"),
    (3, "fadli nurhidayat"),
    (4, "devrian prayasa"),
    (5, "sitti aisyah"),
    (6, "putri zahrah"),
    (7, "aldi"),
    (8, "faril"),
    (9, "uray dhea"),
    (10, "ira riani"),
    (11, "rifky"),
    (12, "hansen"),
    (13, "endarta"),
    (14, "valencia tiara sari"),
    (15, "aditya aprilianto"),
  ]

  employee_data = []

  # Generate data for each employee
  for urutan, nama in employees:
    # Format employee ID
    emp_id = f"K{urutan:03d}"  # Format: K001, K002, etc.

    # Generate email from name (convert to lowercase, replace spaces with dots)
    email = nama.lower().replace(" ", ".") + "@gmail.com"

    # Generate phone number (simple pattern)
    phone = f"08{urutan:010d}"  # Format: 080000000001, 080000000002, etc.

    employee_data.append(
      (
        emp_id,  # id_karyawan
        nama.title(),  # nama_karyawan (proper case)
        email,  # email_karyawan
        phone,  # nomor_hp
        "",  # foto_profile (empty string)
        "2025-01-15",  # tanggal_rekrut (fixed date)
        "aktif",  # status
        1,  # id_departemen (default to 1)
        "Staff",  # posisi (default to Staff)
      )
    )

  # Call the helper function to insert the data
  result = await insert_bulk_employees(employee_data)

  if result["status"] == "error":
    raise HTTPException(status_code=500, detail=result["message"])

  return result


async def insert_bulk_accounts(account_data: list):
  """
  Helper function to insert bulk account data
  :param account_data: List of tuples containing account data
  :return: Dictionary with status and message
  """
  try:
    pool = await get_db()
    total_records = len(account_data)
    inserted_count = 0

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          await conn.begin()

          # Prepare the base query
          base_query = """
              INSERT INTO `akun` (
                  `username`, `passwd`, `roles`, `last_login`, 
                  `id_karyawan`, `device_id`, `status`
              ) VALUES (%s, %s, %s, %s, %s, %s, %s)
          """

          # Insert all records at once
          await cursor.executemany(base_query, account_data)
          inserted_count = total_records

          await conn.commit()
          return {
            "status": "ok",
            "message": f"Successfully inserted {inserted_count} account records",
            "inserted_count": inserted_count,
          }

        except aiomysql.Error as e:
          await conn.rollback()
          return {
            "status": "error",
            "message": f"Database Error: {str(e)}",
            "inserted_count": inserted_count,
          }

  except Exception as e:
    return {
      "status": "error",
      "message": f"Connection Error: {str(e)}",
      "inserted_count": 0,
    }


@app.post("/generate_dummy_accounts")
async def generate_dummy_accounts():
  # List of employees with their data (same as in generate_dummy_employees)
  employees = [
    (1, "marifal safarido"),
    (2, "habta"),
    (3, "fadli nurhidayat"),
    (4, "devrian prayasa"),
    (5, "sitti aisyah"),
    (6, "putri zahrah"),
    (7, "aldi"),
    (8, "faril"),
    (9, "uray dhea"),
    (10, "ira riani"),
    (11, "rifky"),
    (12, "hansen"),
    (13, "endarta"),
    (14, "valencia tiara sari"),
    (15, "aditya aprilianto"),
  ]

  account_data = []

  # Generate account data for each employee
  for urutan, nama in employees:
    # Format employee ID (must match with karyawan table)
    emp_id = f"K{urutan:03d}"

    # Generate username from name (first name lowercase)
    first_name = nama.split()[0].lower()
    username = first_name

    # Password: 1234 (MD5 hash)
    password_hash = "81dc9bdb52d04dc20036dbd8313ed055"  # MD5 of "1234"

    # Role: default to 'karyawan', except for two employee as admin based on urutan
    role = "admin" if urutan in (14, 15) else "karyawan"

    # Current timestamp for last_login
    current_timestamp = "2025-01-15 00:00:00"

    # Device ID. Hp Ak Vivo
    device_id = "eabb6932c16dd71c"

    # Status: all active
    status = "aktif"

    account_data.append(
      (
        username,  # username
        password_hash,  # passwd (MD5 of "1234")
        role,  # roles
        current_timestamp,  # last_login
        emp_id,  # id_karyawan (foreign key)
        device_id,  # device_id
        status,  # status
      )
    )

  # Call the helper function to insert the data
  result = await insert_bulk_accounts(account_data)

  if result["status"] == "error":
    raise HTTPException(status_code=500, detail=result["message"])

  return result
