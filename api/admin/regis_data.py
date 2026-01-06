import aiomysql
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from koneksi import get_db
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
          data = await request.json()

          # 2. AMBIL DEFAULT KUOTA DARI KONFIGURASI
          await cursor.execute(
            "SELECT maks_hari_cuti FROM konfigurasi_aplikasi LIMIT 1"
          )
          config = await cursor.fetchone()
          default_cuti = config["maks_hari_cuti"] if config else 12

          q1 = """
            INSERT INTO karyawan (
              id_karyawan, nama_karyawan, email_karyawan, 
              nomor_hp, tanggal_rekrut, status, id_departemen, posisi,
              jatah_cuti_tahunan
            )
            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            default_cuti,
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
