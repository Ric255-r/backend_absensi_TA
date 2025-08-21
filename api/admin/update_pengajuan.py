import asyncio
from datetime import date, datetime, timedelta
import json
from typing import Optional
import uuid
import aiomysql
from fastapi import APIRouter, Query, Depends, File, Form, Request, HTTPException, Security, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from koneksi import get_db
from fastapi_jwt import (
  JwtAccessBearerCookie,
  JwtAuthorizationCredentials,
  JwtRefreshBearer
)
import pandas as pd
from aiomysql import Error as aiomysqlerror
from jwt_auth import access_security, refresh_security
import calendar
import time
import hashlib
from utils.fn_conv_str import serialize_data
from utils.fn_log import logger

app = APIRouter(
  prefix="/admin"
)

# Ini dari User ke Admin
admin_to_user_conn = []

@app.websocket('/ws-user')
async def ws_absen_user(
  websocket: WebSocket
):
  await websocket.accept()
  admin_to_user_conn.append(websocket)

  try:
    print("Hai WS Nyala")
    await websocket.receive_text()
  except WebSocketDisconnect:
    print("WS Disconnect")
    admin_to_user_conn.remove(websocket)
# End Dari user Ke admin


@app.put('/update_status_absensi')
async def update_status_absensi(
  request: Request
):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:

        try:
          await conn.begin()
          data = await request.json()

          q1 = f"""
            UPDATE absensi SET status_absen = %s {", alasan_penolakan = %s" if "alasan_penolakan" in data else ""} 
            WHERE id_karyawan = %s and id_absensi = %s
          """
          q1_values = [
            data['status_absen'], data['alasan_penolakan'] if 'alasan_penolakan' in data else '-',
            data['id_karyawan'], data['id_absensi']
          ]

          # This is the log message you wanted
          log_message = (
              f"ADMIN  MENGUPDATE STATUS ABSENSI untuk Karyawan [{data['id_karyawan']}] "
              f"menjadi [{data['status_absen']}]"
          )
          logger.info(log_message)
          # --- End of logging ---

          await cursor.execute(q1, q1_values)
          await conn.commit()

          for ws_con in admin_to_user_conn:
            await ws_con.send_text(
              json.dumps({
                "id_karyawan": data['id_karyawan'],
                "status": data['status_absen'],
                "message": f"Absen Anda di{data['status_absen']}"
              })
            )

          return {
            "Success": "Data Berhasil Di Update"
          }

        except aiomysqlerror as e:
          await conn.rollback()
          return JSONResponse(content={"status": "error", "message": f"Database Error {str(e)}"}, status_code=500)
        except HTTPException as e:
          await conn.rollback()
          return JSONResponse(content={"status": "error", "message": f"HTTP Error Error {str(e)}"}, status_code=e.status_code)

      
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500)


def _daterange_inclusive(d1: date, d2: date):
  cur = d1
  while cur <= d2:
    yield cur
    cur += timedelta(days=1)

@app.put('/update_pengajuan')
async def update_pengajuan(
  request: Request
):
  try:
    print("Eksekusi Update Pengajuan")
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:

        try:
          await conn.begin()
          data = await request.json()

          if "alasan_penolakan" in data:
            q3 = f"""
              UPDATE pengajuan_absen SET status = %s, alasan_penolakan = %s
              WHERE id_karyawan = %s and id_pengajuan = %s
            """
            q3_values = [
              data['status'], data['alasan_penolakan'],
              data['id_karyawan'], data['id_pengajuan']
            ]
          else:
            if data['status'] == "approved":
              # Parse Tanggal_Mulai tanggal akhir
              start_d = datetime.strptime(data['tanggal_mulai'], "%Y-%m-%d").date()
              end_d = datetime.strptime(data['tanggal_akhir'], "%Y-%m-%d").date()

              if end_d < start_d:
                raise HTTPException(status_code=400, detail="Tanggal Akhir < Tanggal Mulai")
              
              # Masukin Range Hari ke variable days
              days = list(_daterange_inclusive(start_d, end_d))

              # Ambil Tanggal yang sudah ada pada rentang tersebut
              q1 = """
                SELECT DATE(tanggal_absen) AS tgl
                FROM absensi
                WHERE id_karyawan = %s AND DATE(tanggal_absen) BETWEEN %s AND %s
              """
              await cursor.execute(q1, (data['id_karyawan'] ,start_d, end_d))
              already = {row['tgl'] for row in await cursor.fetchall()}

              # Siapkan Value Yang Belum Ada. Jadi logika ini bkl nambah banyak baris kalo 
              # karyawan buat range tidak hadir. misal tgl 21-23 ga hadir, maka masuk 3 baris ke absensi
              rows = []
              for d in days:
                if d in already: # Sudah ada, maka skip
                  continue
                rows.append((
                  data['id_karyawan'],
                  d.strftime("%Y-%m-%d"),
                  data['tipe_pengajuan'],
                  data['status'],
                ))
              
              if rows:
                q2 = f"""
                  INSERT INTO absensi (id_karyawan, tanggal_absen, pengajuan, status_absen)
                  VALUES(%s, %s, %s, %s)
                """
                # q2_values = [
                #   data['id_karyawan'], data['tanggal_mulai'], data['tipe_pengajuan'], data['status']
                # ]
                # Insert Batch Sekali Jalan
                await cursor.executemany(q2, rows)

            q3 = f"""
              UPDATE pengajuan_absen SET status = %s
              WHERE id_karyawan = %s and id_pengajuan = %s
            """
            q3_values = [
              data['status'], data['id_karyawan'], data['id_pengajuan']
            ]

          await cursor.execute(q3, q3_values)
          await conn.commit()

          for ws_con in admin_to_user_conn:
            await ws_con.send_text(
              json.dumps({
                "id_karyawan": data['id_karyawan'],
                "status": data['status'],
                "message": f"Pengajuan Anda telah di{data['status']}"
              })
            )



          return {
            "Success": "Data Berhasil Di Update"
          }


        except aiomysqlerror as e:
          await conn.rollback()
          return JSONResponse(content={"status": "error", "message": f"Database Error {str(e)}"}, status_code=500)
        except HTTPException as e:
          await conn.rollback()
          return JSONResponse(content={"status": "error", "message": f"HTTP Error Error {str(e)}"}, status_code=e.status_code)

      
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500)