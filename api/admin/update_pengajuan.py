from datetime import date, datetime, timedelta
import json
import aiomysql
from fastapi import APIRouter, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from koneksi import get_db
from aiomysql import Error as aiomysqlerror
from utils.fn_log import logger

app = APIRouter(prefix="/admin")

# Ini dari User ke Admin
admin_to_user_conn = []


@app.websocket("/ws-user")
async def ws_absen_user(websocket: WebSocket):
  await websocket.accept()
  admin_to_user_conn.append(websocket)

  try:
    print("Hai WS Nyala")
    await websocket.receive_text()
  except WebSocketDisconnect:
    print("WS Disconnect")
    admin_to_user_conn.remove(websocket)


# End Dari user Ke admin
@app.put("/update_status_absensi")
async def update_status_absensi(
  request: Request,
  is_bulk: bool = False,
):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          await conn.begin()
          data = await request.json()

          if is_bulk:
            # Jika Massive Update
            for item in data["updated_bulk_data"]:
              q1 = f"""
                UPDATE absensi SET status_absen = %s {", alasan_penolakan = %s" if "alasan_penolakan" in item else ""} 
                WHERE id_karyawan = %s and id_absensi = %s
              """
              q1_values = [
                item["status_absen"],
                item["alasan_penolakan"] if "alasan_penolakan" in item else "-",
                item["id_karyawan"],
                item["id_absensi"],
              ]
              await cursor.execute(q1, q1_values)
              # This is the log message you wanted
              log_message = (
                f"ADMIN  MENGUPDATE STATUS ABSENSI untuk Karyawan [{item['id_karyawan']}] "
                f"menjadi [{item['status_absen']}]"
              )
              logger.info(log_message)

              for ws_con in admin_to_user_conn:
                await ws_con.send_text(
                  json.dumps(
                    {
                      "id_karyawan": item["id_karyawan"],
                      "status": item["status_absen"],
                      "message": f"Absen Anda di{item['status_absen']}",
                    }
                  )
                )
          else:
            q1 = f"""
              UPDATE absensi SET status_absen = %s {", alasan_penolakan = %s" if "alasan_penolakan" in data else ""} 
              WHERE id_karyawan = %s and id_absensi = %s
            """
            q1_values = [
              data["status_absen"],
              data["alasan_penolakan"] if "alasan_penolakan" in data else "-",
              data["id_karyawan"],
              data["id_absensi"],
            ]
            await cursor.execute(q1, q1_values)

            # This is the log message you wanted
            log_message = (
              f"ADMIN  MENGUPDATE STATUS ABSENSI untuk Karyawan [{data['id_karyawan']}] "
              f"menjadi [{data['status_absen']}]"
            )
            logger.info(log_message)
            # --- End of logging ---

            for ws_con in admin_to_user_conn:
              await ws_con.send_text(
                json.dumps(
                  {
                    "id_karyawan": data["id_karyawan"],
                    "status": data["status_absen"],
                    "message": f"Absen Anda di{data['status_absen']}",
                  }
                )
              )

          await conn.commit()

          return {"Success": "Data Berhasil Di Update"}

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


def _daterange_inclusive(d1: date, d2: date):
  cur = d1
  while cur <= d2:
    yield cur
    cur += timedelta(days=1)


@app.put("/update_pengajuan")
async def update_pengajuan(request: Request):
  try:
    print("Eksekusi Update Pengajuan")
    pool = await get_db()
    data = await request.json()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          await conn.begin()

          # --- CASE 1: The request is being REJECTED ---
          if data["alasan_penolakan"] is not None:
            print("Alasan Penlakan")
            update_query = """
              UPDATE pengajuan_absen
              SET status = %s, alasan_penolakan = %s
              WHERE id_karyawan = %s AND id_pengajuan = %s
            """
            update_values = (
              data["status"],
              data["alasan_penolakan"],
              data["id_karyawan"],
              data["id_pengajuan"],
            )
            await cursor.execute(update_query, update_values)

          # --- CASE 2: The request is being APPROVED ---
          elif data["status"] == "approved":
            print("approved")
            # Parse start and end dates
            start_d = datetime.strptime(data["tanggal_mulai"], "%Y-%m-%d").date()
            end_d = datetime.strptime(data["tanggal_akhir"], "%Y-%m-%d").date()

            if end_d < start_d:
              raise HTTPException(
                status_code=400, detail="Tanggal Akhir < Tanggal Mulai"
              )

            # Get all dates in the range
            days_in_range = list(_daterange_inclusive(start_d, end_d))

            # Find which dates already have an attendance record
            q_check_existing = """
              SELECT DATE(tanggal_absen) AS tgl FROM absensi
              WHERE id_karyawan = %s AND DATE(tanggal_absen) BETWEEN %s AND %s
            """
            await cursor.execute(
              q_check_existing, (data["id_karyawan"], start_d, end_d)
            )
            existing_dates = {row["tgl"] for row in await cursor.fetchall()}

            # Prepare new rows for dates that DON'T exist yet
            rows_to_insert = []
            for d in days_in_range:
              if d in existing_dates:
                continue  # Skip if record already exists
              rows_to_insert.append(
                (
                  data["id_karyawan"],
                  d.strftime("%Y-%m-%d"),
                  d.strftime("%Y-%m-%d"),
                  0.0,
                  0.0,
                  "no-foto",
                  data["tipe_pengajuan"],
                  data["status"],
                )
              )

            # If there are new rows to insert, execute the batch insert
            if rows_to_insert:
              q_insert_absensi = """
                  INSERT INTO absensi (
                    id_karyawan, tanggal_absen, check_in, 
                    latitude_checkin, longitude_checkin, foto_checkin, 
                    pengajuan, status_absen
                  )
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
              """
              await cursor.executemany(q_insert_absensi, rows_to_insert)

            # Finally, update the status of the original submission
            update_query = """
                UPDATE pengajuan_absen SET status = %s
                WHERE id_karyawan = %s AND id_pengajuan = %s
            """
            update_values = (data["status"], data["id_karyawan"], data["id_pengajuan"])
            await cursor.execute(update_query, update_values)

          # --- CASE 3 (Optional): Handle other statuses if necessary ---
          else:
            print("else")
            # For statuses like "pending", etc., you might only need to update the status
            update_query = """
                UPDATE pengajuan_absen SET status = %s
                WHERE id_karyawan = %s AND id_pengajuan = %s
            """
            update_values = (data["status"], data["id_karyawan"], data["id_pengajuan"])
            await cursor.execute(update_query, update_values)

          await conn.commit()

          # Send WebSocket notification
          for ws_con in admin_to_user_conn:
            await ws_con.send_text(
              json.dumps(
                {
                  "id_karyawan": data["id_karyawan"],
                  "status": data["status"],
                  "message": f"Pengajuan Anda telah di-{data['status']}",
                }
              )
            )

          return {"Success": "Data Berhasil Di Update"}

        except (aiomysql.Error, HTTPException) as e:
          await conn.rollback()
          status_code = e.status_code if isinstance(e, HTTPException) else 500
          return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=status_code,
          )

  except Exception as e:
    return JSONResponse(
      content={"status": "error", "message": f"Koneksi Error: {str(e)}"},
      status_code=500,
    )
