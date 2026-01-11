import asyncio
from datetime import timedelta
import random
from fastapi import APIRouter, HTTPException
import pandas as pd
from koneksi import get_db
from services.seeders.helpers import (
  get_employee_schedule_map,
  get_employees,
  get_master_shift_times,
  get_lateness_tolerance,
  insert_bulk_accounts,
  insert_bulk_attendance,
  insert_bulk_hari_libur,
  insert_bulk_master_shift,
  insert_bulk_employee_schedule,
  insert_bulk_employees,
)

app = APIRouter(prefix="/seed")


# --- 3. Main Function ---
@app.post("/generate_dummy_attendance")
async def generate_dummy_attendance():
  try:
    pool = await get_db()

    # Eksekusi parallel untuk mempercepat
    config_task = get_lateness_tolerance(pool)
    master_shift_task = get_master_shift_times(pool)
    employees_task = get_employees(pool)
    emp_schedule_task = get_employee_schedule_map(pool)

    config, master_shift_map, employees, emp_schedule_map = await asyncio.gather(
      config_task, master_shift_task, employees_task, emp_schedule_task
    )

    if not config:
      raise HTTPException(status_code=500, detail="Config Kosong")
    if not master_shift_map:
      raise HTTPException(status_code=500, detail="Jadwal Kosong")
    if not employees:
      raise HTTPException(status_code=500, detail="Data Karyawan Kosong")
    if not emp_schedule_map:
      raise HTTPException(status_code=500, detail="Jadwal Karyawan Kosong")

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
      foto = foto_by_emp_id.get(emp_id, emp["foto"])

      # Cari shift spesifik karyawan untuk hari ini
      emp_schedule_key = (emp_id, indo_day)
      if emp_schedule_key not in emp_schedule_map:
        continue
      emp_shift = emp_schedule_map[emp_schedule_key]  # 'pagi' atau 'sore'

      # Cari Jadwal master untuk (Hari Ini + Shift Karyawan Ini)
      schedule_key = (indo_day, emp_shift)

      # Jika tidak ada jadwal (misal Minggu atau shift pagi libur di hari Jumat), skip
      if schedule_key not in master_shift_map:
        continue

      # Jam mulai shift (timedelta)
      shift_start_delta = master_shift_map[schedule_key]

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


@app.post("/generate_dummy_employees")
async def generate_dummy_employees():
  # List of employees with their data
  employees = [
    (1, "marifal safarido", 6, "Staff", "pagi"),
    (2, "habta", 6, "Staff", "pagi"),
    (3, "fadli nurhidayat", 6, "Staff", "sore"),
    (4, "devrian prayasa", 6, "Staff", "sore"),
    (5, "sitti aisyah", 6, "Kasir", "pagi"),
    (6, "putri zahrah", 6, "Kasir", "sore"),
    (7, "aldi", 2, "Staff", "pagi"),
    (8, "faril", 2, "Staff", "sore"),
    (9, "uray dhea", 2, "Kasir", "pagi"),
    (10, "ira riani", 2, "Kasir", "sore"),
    (11, "rifky", 1, "Staff", "pagi"),
    (12, "hansen", 1, "Staff", "pagi"),
    (13, "endarta", 1, "Staff", "sore"),
    (14, "valencia tiara sari", 4, "Kasir", "pagi"),
    (15, "aditya aprilianto", 4, "Kasir", "sore"),
  ]

  employee_data = []
  schedule_data = []
  schedule_days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]

  # Generate data for each employee
  for urutan, nama, id_departemen, posisi, kode_shift in employees:
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
        id_departemen,  # id_departemen (default to 1)
        posisi,  # posisi (default to Staff)
      )
    )

    for hari in schedule_days:
      schedule_data.append(
        (
          emp_id,  # id_karyawan
          hari,  # hari
          kode_shift,  # kode_shift
        )
      )

  # Call the helper function to insert the data
  result = await insert_bulk_employees(employee_data)

  if result["status"] == "error":
    raise HTTPException(status_code=500, detail=result["message"])

  schedule_result = await insert_bulk_employee_schedule(schedule_data)

  if schedule_result["status"] == "error":
    raise HTTPException(status_code=500, detail=schedule_result["message"])

  return {
    "status": "ok",
    "message": "Successfully inserted employee and schedule records",
    "employee_inserted_count": result["inserted_count"],
    "schedule_inserted_count": schedule_result["inserted_count"],
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


@app.post("/generate_dummy_master_shift")
async def generate_dummy_master_shift():
  master_shift_data = [
    ("pagi", "08:00:00", "16:00:00", "Senin"),
    ("sore", "13:00:00", "21:00:00", "Senin"),
    ("pagi", "08:00:00", "16:00:00", "Selasa"),
    ("sore", "13:00:00", "21:00:00", "Selasa"),
    ("pagi", "08:00:00", "16:00:00", "Rabu"),
    ("sore", "13:00:00", "21:00:00", "Rabu"),
    ("pagi", "08:00:00", "16:00:00", "Kamis"),
    ("sore", "13:00:00", "21:00:00", "Kamis"),
    ("pagi", "08:00:00", "16:00:00", "Jumat"),
    ("sore", "13:00:00", "21:00:00", "Jumat"),
    ("pagi", "08:00:00", "16:00:00", "Sabtu"),
    ("sore", "13:00:00", "21:00:00", "Sabtu"),
  ]

  result = await insert_bulk_master_shift(master_shift_data)

  if result["status"] == "error":
    raise HTTPException(status_code=500, detail=result["message"])

  return result


@app.post("/generate_dummy_hari_libur")
async def generate_dummy_hari_libur():
  holiday_data = [
    ("2026-02-16", "Cuti Bersama Tahun Baru Imlek 2577 Kongzili", "cuti_bersama"),
    ("2026-03-18", "Cuti Bersama Hari Suci Nyepi (Tahun Baru Saka 1948)", "cuti_bersama"),
    ("2026-03-20", "Cuti Bersama Idul Fitri 1447 Hijriah", "cuti_bersama"),
    ("2026-03-23", "Cuti Bersama Idul Fitri 1447 Hijriah", "cuti_bersama"),
    ("2026-03-24", "Cuti Bersama Idul Fitri 1447 Hijriah", "cuti_bersama"),
    ("2026-05-15", "Cuti Bersama Kenaikan Yesus Kristus", "cuti_bersama"),
    ("2026-05-28", "Cuti Bersama Idul Adha 1447 Hijriah", "cuti_bersama"),
    ("2026-12-24", "Cuti Bersama Kelahiran Yesus Kristus (Natal)", "cuti_bersama"),
  ]

  result = await insert_bulk_hari_libur(holiday_data)

  if result["status"] == "error":
    raise HTTPException(status_code=500, detail=result["message"])

  return result
