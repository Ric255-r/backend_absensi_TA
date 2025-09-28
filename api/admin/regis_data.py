import aiomysql
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from koneksi import get_db
import pandas as pd
from aiomysql import Error as aiomysqlerror
import hashlib

app = APIRouter(prefix="/admin")


@app.post("/regis_karyawan")
async def regis_karyawan(request: Request):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          # 1. Start Transaction
          await conn.begin()

          # 2. Execute querynya
          data = await request.json()
          q1 = """
            INSERT INTO karyawan (
              id_karyawan, nama_karyawan, email_karyawan, 
              nomor_hp, tanggal_rekrut, status, id_departemen, posisi
            )
            VALUES(%s, %s, %s, %s, %s, %s, %s, %s)
          """
          q1_values = (
            data["id_karyawan"],
            data["nama_karyawan"],
            data["email_karyawan"],
            data["nomor_hp"],
            data["tanggal_rekrut"],
            data["status"],
            data["id_departemen"],
            data["posisi"],
          )
          await cursor.execute(q1, q1_values)
          # 3. Klo Sukses, dia bkl save ke db
          await conn.commit()

          return {"status": "ok", "message": "Sukses Simpan Data"}

        except aiomysqlerror as e:
          await conn.rollback()
          return JSONResponse(
            content={"status": "error", "message": f"Database Error {str(e)}"},
            status_code=500,
          )
        except HTTPException as e:
          await conn.rollback()
          return JSONResponse(
            content={"status": "error", "message": f"HTTP Error Error {str(e)}"},
            status_code=e.status_code,
          )

  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500
    )


@app.post("/regis_akun")
async def regis_akun(request: Request):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          # 1. Start Transaction
          await conn.begin()

          # 2. Execute querynya
          data = await request.json()
          q1 = """
            INSERT INTO akun (
              username, passwd, roles, id_karyawan, status
            )
            VALUES(%s, %s, %s, %s, %s)
          """
          passwd = hashlib.md5(str(data["passwd"]).encode())
          q1_values = (
            data["username"],
            passwd.hexdigest(),
            data["roles"],
            data["id_karyawan"],
            data["status"],
          )
          await cursor.execute(q1, q1_values)
          # 3. Klo Sukses, dia bkl save ke db
          await conn.commit()

          return {"status": "ok", "message": "Sukses Simpan Data"}

        except aiomysqlerror as e:
          await conn.rollback()
          return JSONResponse(
            content={"status": "error", "message": f"Database Error {str(e)}"},
            status_code=500,
          )
        except HTTPException as e:
          await conn.rollback()
          return JSONResponse(
            content={"status": "error", "message": f"HTTP Error Error {str(e)}"},
            status_code=e.status_code,
          )

  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500
    )


@app.post("/regis_departemen")
async def regis_departemen(request: Request):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          # 1. Start Transaction
          await conn.begin()

          # 2. Execute querynya
          data = await request.json()
          q1 = """
            INSERT INTO departemen (
              nama_departemen
            )
            VALUES(%s)
          """
          await cursor.execute(q1, data["nama_departemen"])
          # 3. Klo Sukses, dia bkl save ke db
          await conn.commit()

          return {"status": "ok", "message": "Sukses Simpan Data"}

        except aiomysqlerror as e:
          await conn.rollback()
          return JSONResponse(
            content={"status": "error", "message": f"Database Error {str(e)}"},
            status_code=500,
          )
        except HTTPException as e:
          await conn.rollback()
          return JSONResponse(
            content={"status": "error", "message": f"HTTP Error Error {str(e)}"},
            status_code=e.status_code,
          )

  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500
    )


@app.post("/regis_jadwal_krywn")
async def regis_jadwal(request: Request):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          # 1. Start Transaction
          await conn.begin()

          # 2. Execute querynya
          data = await request.json()
          q1 = """
            INSERT INTO jadwal_karyawan (
              id_karyawan, id_jadwal
            )
            VALUES(%s, %s)
          """
          q1_values = (data["id_karyawan"], data["id_jadwal"])
          await cursor.execute(q1, q1_values)
          # 3. Klo Sukses, dia bkl save ke db
          await conn.commit()

          return {"status": "ok", "message": "Sukses Simpan Data"}

        except aiomysqlerror as e:
          await conn.rollback()
          return JSONResponse(
            content={"status": "error", "message": f"Database Error {str(e)}"},
            status_code=500,
          )
        except HTTPException as e:
          await conn.rollback()
          return JSONResponse(
            content={"status": "error", "message": f"HTTP Error Error {str(e)}"},
            status_code=e.status_code,
          )

  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500
    )


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
  # List of employee IDs
  employee_ids = [
    "K003",
    "K005",
    "K006",
    "K007",
    "K008",
    "K009",
    "K010",
    "K011",
    "K012",
  ]

  # Date range: July 1 to July 25, 2025
  start_date = pd.Timestamp("2025-07-01")
  end_date = pd.Timestamp("2025-07-25")
  date_range = pd.date_range(start_date, end_date)

  attendance_data = []

  # Generate data for each employee for each date
  for date in date_range:
    for emp_id in employee_ids:
      # Format the date strings
      date_str = date.strftime("%Y-%m-%d")
      is_late = 1 if emp_id == "K005" else 0  # K005 is always late

      attendance_data.append(
        (
          emp_id,
          f"{date_str} 03:00:00",  # tanggal_absen
          f"{date_str} 10:00:00",  # check_in (or 11:00 for K005)
          f"{date_str} 18:00:34",  # check_out
          -0.03020289202263597,  # latitude_checkin
          109.3217448800716,  # longitude_checkin
          -0.03020289202263597,  # latitude_checkout
          109.3217448800716,  # longitude_checkout
          "29364861-3c44-423b-b904-19b41481bcae.png",  # foto_checkin
          "62be7b06-3cb2-41dc-ab55-1e92c17b465c.png",  # foto_checkout
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
