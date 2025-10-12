import json
import os
import uuid
import aiomysql
from fastapi import APIRouter, Request, HTTPException, Security, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from koneksi import get_db
from fastapi_jwt import JwtAuthorizationCredentials
from aiomysql import Error as aiomysqlerror
from jwt_auth import access_security
from api.admin.get_data import absensi_connection
from api.users.absensi import save_upload_file

app = APIRouter(prefix="/absen_tidakhadir")

FOTO_TIDAK_HADIR = "api/images/tidak_hadir"


@app.get("/foto_tidakhadir/{filename}")
def get_foto_tidakhadir(filename: str):
  img_path = os.path.join(FOTO_TIDAK_HADIR, filename)
  return FileResponse(img_path, media_type="image/png")


@app.get("/")
async def get_data(user: JwtAuthorizationCredentials = Security(access_security)):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          await cursor.execute(
            "SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;"
          )

          q1 = "SELECT * FROM pengajuan_absen WHERE id_karyawan = %s"
          await cursor.execute(q1, user["id_karyawan"])

          items = await cursor.fetchall()
          return items
        except aiomysqlerror as e:
          return JSONResponse(
            content={"status": "error", "message": f"Database Error {str(e)}"},
            status_code=500,
          )
        except HTTPException as e:
          return JSONResponse(
            content={"status": "error", "message": f"HTTP Error Error {str(e)}"},
            status_code=e.status_code,
          )

  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500
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
              return JSONResponse(
                content={
                  "status": "error",
                  "message": "Anda sudah melakukan absen hari ini, Anda Yakin ingin Mengoverride?",
                },
                status_code=400,
              )

          # saveFile. cek key foto_lampiran ada atau nd
          if "foto_lampiran" in data:
            filename = f"{uuid.uuid4()}.png"
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
            filename if "foto_lampiran" in data else "",
            data["keterangan"],
          )
          await cursor.execute(q1, q1_values)
          await conn.commit()

          for ws_con in absensi_connection:
            await ws_con.send_text(
              json.dumps({"message": f"ada pengajuan {data['tipe_pengajuan']} baru"})
            )

          return {"Sukses": "Pengajuan di Minta"}

        except aiomysqlerror as e:
          return JSONResponse(
            content={"status": "error", "message": f"Database Error {str(e)}"},
            status_code=500,
          )
        except HTTPException as e:
          return JSONResponse(
            content={"status": "error", "message": f"HTTP Error Error {str(e)}"},
            status_code=e.status_code,
          )

  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500
    )
