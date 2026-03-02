import aiomysql
from fastapi import APIRouter, HTTPException
import pandas as pd
from api_legacy.users.absensi import _get_lateness_tolerance
from koneksi import get_db
from aiomysql import Error as aiomysqlerror
import random

app = APIRouter(prefix="/seed")


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


@app.post("/generate_dummy_attendance")
async def generate_dummy_attendance():
  try:
    pool = await get_db()
    config = await _get_lateness_tolerance(pool)

    if not config:
      # Kasus jika tabel konfigurasi_aplikasi kosong
      raise HTTPException(
        status_code=500,
        detail="Tidak dapat mengambil konfigurasi. Tabel 'konfigurasi_aplikasi' mungkin kosong.",
      )

    # 2. Simpan nilai toleransi dalam menit
    lateness_tolerance_minutes = config["toleransi_terlambat"]

  except Exception as e:
    # Menangani error jika koneksi db atau query gagal
    raise HTTPException(
      status_code=500, detail=f"Database error saat mengambil konfigurasi: {str(e)}"
    )
  # --- Modifikasi Selesai ---

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

  # Date range: July 1 to July 25, 2025
  start_date = pd.Timestamp("2025-12-01")
  end_date = pd.Timestamp("2025-12-31")
  date_range = pd.date_range(start_date, end_date)

  attendance_data = []

  # Generate data for each employee for each date
  for date in date_range:
    # Skip Sundays (Monday=0 ... Sunday=6)
    if date.weekday() == 6:
      continue
    for emp_id, foto in employee_attendance_data:
      # Format the date strings
      date_str = date.strftime("%Y-%m-%d")
      hour_val = 10
      minute_val = random.randint(0, 35)
      second_val = random.randint(0, 59)

      # 2. Create your string using these variables
      time_attend_str = (
        f"{hour_val}:{str(minute_val).zfill(2)}:{str(second_val).zfill(2)}"
      )

      total_lateness_in_minutes = minute_val + (second_val / 60)

      #  Bandingkan dengan toleransi dari database
      #    Jika total keterlambatan > toleransi, maka is_late = 1
      #    Contoh: jika toleransi 12 Menit, maka 12.01 sudah telat (is_late = 1)
      #            tetapi 12.00 atau 11.99 belum telat (is_late = 0)
      is_late = 1 if total_lateness_in_minutes > lateness_tolerance_minutes else 0

      attendance_data.append(
        (
          emp_id,
          f"{date_str} {time_attend_str}",  # tanggal_absen
          f"{date_str} {time_attend_str}",  # check_in
          f"{date_str} 18:00:34",  # check_out
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

  # Call the helper function to insert the data
  result = await insert_bulk_attendance(attendance_data)

  if result["status"] == "error":
    raise HTTPException(status_code=500, detail=result["message"])

  return result


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
