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

          await broadcast_pengajuan_created(
            {
              "id_pengajuan": cursor.lastrowid,
              "id_karyawan": user["id_karyawan"],
              "tipe_pengajuan": data["tipe_pengajuan"],
              "tanggal_mulai": data["tanggal_mulai"],
              "tanggal_akhir": data["tanggal_akhir"],
              "foto_lampiran": filename if "foto_lampiran" in data else "",
              "keterangan": data["keterangan"],
            },
            pool,
          )

          return {"Sukses": "Pengajuan di Minta"}

        except aiomysqlerror as e:
          await conn.rollback()
          print("Database Error", str(e))
          return JSONResponse(
            content={"status": "error", "message": f"Database Error {str(e)}"},
            status_code=500,
          )
        except HTTPException as e:
          await conn.rollback()
          print("HTTP Error Error", str(e))
          return JSONResponse(
            content={"status": "error", "message": f"HTTP Error Error {str(e)}"},
            status_code=e.status_code,
          )

  except Exception as e:
    print("Koneksi Error", str(e))
    return JSONResponse(
      content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500
    )


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
    "event": "pengajuan_created",
    "message": f"{data_karyawan['nama_karyawan']} membuat pengajuan {pa_row['tipe_pengajuan']}",
    "effective_date": str(pa_row["tanggal_mulai"]),  # <-- kunci
    "payload": {
      "id_pengajuan": pa_row["id_pengajuan"],
      "nama_karyawan": data_karyawan["nama_karyawan"],
      "tipe_pengajuan": pa_row["tipe_pengajuan"],
      "tanggal_mulai": str(pa_row["tanggal_mulai"]),
      "tanggal_akhir": str(pa_row["tanggal_akhir"]),
      "lampiran": pa_row.get("lampiran", "") or "",
      "keterangan": pa_row.get("keterangan", "") or "",
      "status": "pending",
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
