import asyncio
import json
import os
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
from api.admin.get_data import absensi_connection

app = APIRouter(
  prefix="/absen_tidakhadir"
)

FOTO_TIDAK_HADIR = "api/images/tidak_hadir"

@app.get('/foto_tidakhadir/{filename}')
def get_foto_tidakhadir(filename: str):
  img_path = os.path.join(FOTO_TIDAK_HADIR, filename)
  return FileResponse(img_path, media_type='image/png')

@app.get('/')
async def get_data(
  user: JwtAuthorizationCredentials = Security(access_security)
):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          await cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;")

          q1 = "SELECT * FROM pengajuan_absen WHERE id_karyawan = %s"
          await cursor.execute(q1, user['id_karyawan'])

          items = await cursor.fetchall()
          return items
        except aiomysqlerror as e:
          return JSONResponse(content={"status": "error", "message": f"Database Error {str(e)}"}, status_code=500)
        except HTTPException as e:
          return JSONResponse(content={"status": "error", "message": f"HTTP Error Error {str(e)}"}, status_code=e.status_code)

      
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500)

@app.post('/store_data')
async def store_data(
  request: Request,
  user: JwtAuthorizationCredentials = Security(access_security)
):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:

        try:
          await conn.begin()
          data = await request.form()

          #saveFile. cek key foto_lampiran ada atau nd
          if 'foto_lampiran' in data:
            filename = f"{uuid.uuid4()}.png"
            file_location = os.path.join(FOTO_TIDAK_HADIR, filename)

            content = await data['foto_lampiran'].read()
            with open(file_location, "wb") as f:
              f.write(content)

          q1 = """
            INSERT INTO pengajuan_absen(id_karyawan, tipe_pengajuan, tanggal_mulai, tanggal_akhir, foto_lampiran, keterangan)
            VALUES(%s, %s, %s, %s, %s, %s)
          """
          q1_values = (
            user['id_karyawan'], data['tipe_pengajuan'], data['tanggal_mulai'], data['tanggal_akhir'],
            filename if 'foto_lampiran' in data else '', data['keterangan']
          )
          await cursor.execute(q1, q1_values)
          await conn.commit()

          for ws_con in absensi_connection:
            await ws_con.send_text(
              json.dumps({
                "message": f"ada pengajuan {data['tipe_pengajuan']} baru"
              })
            )

          return {
            "Sukses": "Pengajuan di Minta"
          }

        except aiomysqlerror as e:
          return JSONResponse(content={"status": "error", "message": f"Database Error {str(e)}"}, status_code=500)
        except HTTPException as e:
          return JSONResponse(content={"status": "error", "message": f"HTTP Error Error {str(e)}"}, status_code=e.status_code)

  except Exception as e:
    return JSONResponse(content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500)
  


