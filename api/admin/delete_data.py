import aiomysql
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from koneksi import get_db
from aiomysql import Error as aiomysqlerror

app = APIRouter(prefix="/admin")


@app.delete("/delete_karyawan/{id_karyawan}")
async def delete_karyawan(id_karyawan: str):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          # 1. Start Transaction
          await conn.begin()

          q1 = """
            DELETE FROM karyawan WHERE id_karyawan = %s
          """
          await cursor.execute(q1, id_karyawan)
          # 3. Klo Sukses, dia bkl save ke db
          await conn.commit()

          return {"status": "ok", "message": "Sukses Delete Data"}

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


@app.delete("/delete_akun/{username}")
async def delete_akun(username: str):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          # 1. Start Transaction
          await conn.begin()

          q1 = """
            DELETE FROM akun WHERE username = %s
          """
          await cursor.execute(q1, username)
          # 3. Klo Sukses, dia bkl save ke db
          await conn.commit()

          return {"status": "ok", "message": "Sukses Delete Data"}

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


@app.delete("/delete_departemen/{id_departemen}")
async def delete_departemen(id_departemen: str):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          # 1. Start Transaction
          await conn.begin()

          q1 = """
            DELETE FROM departemen WHERE id_departemen = %s
          """
          await cursor.execute(q1, id_departemen)
          # 3. Klo Sukses, dia bkl save ke db
          await conn.commit()

          return {"status": "ok", "message": "Sukses Delete Data"}

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


@app.delete("/hari_libur/{id_libur}")
async def delete_hari_libur(id_libur: str):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          # 1. Start Transaction
          await conn.begin()

          q1 = """
            DELETE FROM hari_libur WHERE id_libur = %s
          """
          await cursor.execute(q1, id_libur)
          # 3. Klo Sukses, dia bkl save ke db
          await conn.commit()

          return {"status": "ok", "message": "Sukses Delete Data"}

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
