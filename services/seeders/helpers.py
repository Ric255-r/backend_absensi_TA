import aiomysql
from aiomysql import Error as aiomysqlerror
from koneksi import get_db


async def get_lateness_tolerance(pool: aiomysql.Pool):
  async with pool.acquire() as conn:
    async with conn.cursor(aiomysql.DictCursor) as cursor:
      await cursor.execute("SELECT toleransi_terlambat FROM konfigurasi_aplikasi")
      return await cursor.fetchone()


# --- 1. Helper: Ambil Jadwal dengan Key (Hari, Shift) ---
async def get_master_shift_times(pool: aiomysql.Pool):
  """
  Mengambil jam masuk dari tabel jadwal_kerja.
  Return Dict: { ('Senin', 'pagi'): timedelta(08:00:00), ... }
  """
  shift_times = {}
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
        shift_times[key] = row["shift_mulai"]
  return shift_times


# --- 2. Helper: Ambil Data Karyawan & Shift Mereka ---
async def get_employee_schedule_map(pool: aiomysql.Pool):
  """
  Mengambil jadwal spesifik karyawan dari tabel jadwal_mingguan_karyawan.
  Return Dict: { ('K001', 'Senin'): 'pagi', ('K001', 'Selasa'): 'sore', ... }
  """
  emp_schedule_map = {}
  async with pool.acquire() as conn:
    async with conn.cursor(aiomysql.DictCursor) as cursor:
      await cursor.execute(
        "SELECT id_karyawan, hari, kode_shift FROM jadwal_mingguan_karyawan"
      )
      rows = await cursor.fetchall()
      for row in rows:
        # Key: (ID Karyawan, Hari Indo)
        key = (row["id_karyawan"], row["hari"])
        emp_schedule_map[key] = row["kode_shift"]
  return emp_schedule_map


# --- 2b. Helper: Ambil Data Karyawan untuk Absensi ---
async def get_employees(pool: aiomysql.Pool):
  """
  Mengambil data karyawan (tanpa shift).
  Return List[Dict]: [{ "id": "K001", "foto": "..." }, ...]
  """
  async with pool.acquire() as conn:
    async with conn.cursor(aiomysql.DictCursor) as cursor:
      await cursor.execute(
        "SELECT id_karyawan AS id, foto_profile AS foto FROM karyawan"
      )
      return await cursor.fetchall()


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


async def insert_bulk_employee_schedule(schedule_data: list):
  """
  Helper function to insert bulk employee schedule data
  :param schedule_data: List of tuples containing schedule data
  :return: Dictionary with status and message
  """
  try:
    pool = await get_db()
    total_records = len(schedule_data)
    inserted_count = 0

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          await conn.begin()

          base_query = """
              INSERT INTO `jadwal_mingguan_karyawan` (
                  `id_karyawan`, `hari`, `kode_shift`
              ) VALUES (%s, %s, %s)
          """

          await cursor.executemany(base_query, schedule_data)
          inserted_count = total_records

          await conn.commit()
          return {
            "status": "ok",
            "message": f"Successfully inserted {inserted_count} schedule records",
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


async def insert_bulk_master_shift(master_shift_data: list):
  """
  Helper function to insert bulk jadwal_kerja data
  :param master_shift_data: List of tuples containing master shift data
  :return: Dictionary with status and message
  """
  try:
    pool = await get_db()
    total_records = len(master_shift_data)
    inserted_count = 0

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          await conn.begin()

          base_query = """
              INSERT INTO `jadwal_kerja` (
                  `nama_shift`, `shift_mulai`, `shift_selesai`, `hari_dalam_seminggu`
              ) VALUES (%s, %s, %s, %s)
          """

          await cursor.executemany(base_query, master_shift_data)
          inserted_count = total_records

          await conn.commit()
          return {
            "status": "ok",
            "message": f"Successfully inserted {inserted_count} master shift records",
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


async def insert_bulk_hari_libur(holiday_data: list):
  """
  Helper function to insert bulk hari_libur data
  :param holiday_data: List of tuples containing holiday data
  :return: Dictionary with status and message
  """
  try:
    pool = await get_db()
    total_records = len(holiday_data)
    inserted_count = 0

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          await conn.begin()

          base_query = """
              INSERT INTO `hari_libur` (
                  `tanggal`, `keterangan`, `tipe`
              ) VALUES (%s, %s, %s)
          """

          await cursor.executemany(base_query, holiday_data)
          inserted_count = total_records

          await conn.commit()
          return {
            "status": "ok",
            "message": f"Successfully inserted {inserted_count} holiday records",
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
