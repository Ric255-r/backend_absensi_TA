from typing import Optional
import aiomysql
from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import JSONResponse
from koneksi import get_db
from aiomysql import Error as aiomysqlerror
import hashlib

app = APIRouter(prefix="/admin")


@app.put("/update_karyawan")
async def update_karyawan(request: Request):
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
            UPDATE karyawan SET nama_karyawan = %s, email_karyawan = %s, nomor_hp = %s, tanggal_rekrut = %s,
            status = %s, id_departemen = %s, posisi = %s
            WHERE id_karyawan = %s
          """
          q1_values = (
            data["nama_karyawan"],
            data["email_karyawan"],
            data["nomor_hp"],
            data["tanggal_rekrut"],
            data["status"],
            data["id_departemen"],
            data["posisi"],
            data["id_karyawan"],
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


@app.put("/update_akun")
async def update_akun(request: Request):
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
            UPDATE akun SET passwd = %s, roles = %s, id_karyawan = %s, status = %s 
            WHERE username = %s
          """
          passwd = hashlib.md5(str(data["passwd"]).encode())
          q1_values = (
            passwd.hexdigest(),
            data["roles"],
            data["id_karyawan"],
            "aktif" if bool(data["status"]) else "nonaktif",
            data["username"],
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


@app.put("/update_konfigurasi")
async def update_konfigurasi(request: Request):
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
            UPDATE konfigurasi_aplikasi SET toleransi_terlambat = %s, maks_hari_cuti = %s
            WHERE id_pengaturan = %s
          """
          q1_values = (
            data["toleransi_terlambat"],
            data["maks_hari_cuti"],
            data["id_pengaturan"],
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


@app.put("/update_departemen")
async def update_departemen(request: Request):
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
            UPDATE departemen SET nama_departemen = %s
            WHERE id_departemen = %s
          """
          q1_values = (
            data["nama_departemen"],
            data["id_departemen"],
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


@app.put("/jadwal_kerja/{id_jadwal}")
async def update_jadwal(id_jadwal: str, request: Request):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          # 1. Start Transaction
          await conn.begin()
          payload = await request.json()

          q1 = """
            UPDATE jadwal_kerja SET nama_shift = %s, shift_mulai = %s, shift_selesai = %s, hari_dalam_seminggu = %s
            WHERE id_jadwal = %s
          """
          q1_values = (
            payload["nama_shift"],
            payload["shift_mulai"],
            payload["shift_selesai"],
            payload["hari_dalam_seminggu"],
            id_jadwal,
          )
          await cursor.execute(q1, q1_values)
          # 3. Klo Sukses, dia bkl save ke db
          await conn.commit()

          return {"status": "ok", "message": "Sukses Update Data"}

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


@app.put("/unbind_device/{username}")
async def unbind_device(username: str):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          # 1. Start Transaction
          await conn.begin()

          q1 = """
            UPDATE akun SET device_id = NULL WHERE username = %s
          """
          await cursor.execute(q1, username)
          # 3. Klo Sukses, dia bkl save ke db
          await conn.commit()

          return {"status": "ok", "message": "Sukses Unbind Device Data"}

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


@app.put("/hari_libur/{id_libur}")
async def update_hari_libur(id_libur: str, request: Request):
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
            UPDATE hari_libur SET tanggal = %s, keterangan = %s, tipe = %s
            WHERE id_libur = %s
          """
          q1_values = (
            data["tanggal"],
            data["keterangan"],
            data["tipe"],
            id_libur,
          )
          await cursor.execute(q1, q1_values)
          # 3. Klo Sukses, dia bkl save ke db
          await conn.commit()

          return {"status": "ok", "message": "Sukses Update Data"}

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


@app.put("/upsert_jadwal_karyawan")
async def upsert_jadwal_karyawan(
  request: Request, id_karyawan: Optional[str] = Query(None)
):
  try:
    if not id_karyawan:
      return JSONResponse(
        content={
          "status": "error",
          "message": "id_karyawan wajib diisi di query param",
        },
        status_code=400,
      )

    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          await conn.begin()

          payloads = await request.json()  # array of objects
          if not isinstance(payloads, list) or len(payloads) == 0:
            return JSONResponse(
              content={
                "status": "error",
                "message": "Payload harus berupa array dan tidak boleh kosong",
              },
              status_code=400,
            )

          # Validasi sederhana + normalisasi
          values = []
          for i, d in enumerate(payloads):
            if not isinstance(d, dict):
              return JSONResponse(
                content={"status": "error", "message": f"Item index {i} harus object"},
                status_code=400,
              )

            hari = d.get("hari")
            kode_shift = d.get("kode_shift")

            if not hari or not kode_shift:
              return JSONResponse(
                content={
                  "status": "error",
                  "message": f"Item index {i} wajib punya 'hari' dan 'kode_shift'",
                },
                status_code=400,
              )

            # Optional: validasi value enum (biar errornya lebih jelas daripada error DB)
            if hari not in [
              "Senin",
              "Selasa",
              "Rabu",
              "Kamis",
              "Jumat",
              "Sabtu",
              "Minggu",
            ]:
              return JSONResponse(
                content={
                  "status": "error",
                  "message": f"Item index {i}: hari tidak valid ({hari})",
                },
                status_code=400,
              )

            if kode_shift not in ["pagi", "sore"]:
              return JSONResponse(
                content={
                  "status": "error",
                  "message": f"Item index {i}: kode_shift tidak valid ({kode_shift})",
                },
                status_code=400,
              )

            values.append((id_karyawan, hari, kode_shift))

          q = """
            INSERT INTO jadwal_mingguan_karyawan (id_karyawan, hari, kode_shift)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
              kode_shift = VALUES(kode_shift)
          """

          await cursor.executemany(q, values)

          await conn.commit()
          return {
            "status": "ok",
            "message": "Sukses Upsert Data",
            "affected_rows": cursor.rowcount,
          }

        except aiomysqlerror as e:
          await conn.rollback()
          return JSONResponse(
            content={"status": "error", "message": f"Database Error: {str(e)}"},
            status_code=500,
          )
        except Exception as e:
          await conn.rollback()
          return JSONResponse(
            content={"status": "error", "message": f"Unexpected Error: {str(e)}"},
            status_code=500,
          )

  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": f"Koneksi Error {str(e)}"},
      status_code=500,
    )
