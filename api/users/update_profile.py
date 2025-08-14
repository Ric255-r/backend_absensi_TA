import asyncio
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
import os
from api.admin.get_data import absensi_connection

app = APIRouter(
  prefix="/users"
)
FOTO_PROFILE = "api/images/foto_profile"

@app.get('/foto_profile/{filename}')
def get_foto_checkin(filename: str):
  img_path = os.path.join(FOTO_PROFILE, filename)
  return FileResponse(img_path, media_type='image/png')

@app.post('/update_profile')
async def update_profile(
  request: Request,
  user: JwtAuthorizationCredentials = Security(access_security),
):
  
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:

        try:

          # 1. Start Transaction
          await conn.begin()

          # 2. Execute querynya
          data = await request.form()
          filename = "-"
          if "foto_profile" in data:
            filename = f"{uuid.uuid4()}.png"
            file_location = os.path.join(FOTO_PROFILE, filename)

            #saveFile
            content = await data['foto_profile'].read()
            with open(file_location, "wb") as f:
              f.write(content)

          q1 = """
            UPDATE karyawan SET nama_karyawan = %s, email_karyawan = %s, nomor_hp = %s, foto_profile = %s
            WHERE id_karyawan = %s
          """
          q1_values = (
            data['nama_karyawan'], data['email_karyawan'], data['nomor_hp'], filename, user['id_karyawan']
          )
          await cursor.execute(q1, q1_values)
          # 3. Klo Sukses, dia bkl save ke db
          await conn.commit()

          return {
            "status": "ok",
            "message": "Sukses Simpan Data"
          }
          

        except aiomysqlerror as e:
          await conn.rollback()
          return JSONResponse(content={"status": "error", "message": f"Database Error {str(e)}"}, status_code=500)
        except HTTPException as e:
          await conn.rollback()
          return JSONResponse(content={"status": "error", "message": f"HTTP Error Error {str(e)}"}, status_code=e.status_code)

  except Exception as e:
    return JSONResponse(content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500)
  
@app.put('/update_password')
async def update_password(
  request: Request,
  user: JwtAuthorizationCredentials = Security(access_security),
):
  
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:

        try:

          # 1. Start Transaction
          await conn.begin()

          # 2. Execute querynya
          data = await request.json()
          old_pass = hashlib.md5(str(data['old_pass']).encode())


          q1 = """
            SELECT * FROM akun WHERE id_karyawan = %s
          """
          await cursor.execute(q1, user['id_karyawan'])
          item1 = await cursor.fetchone()

          if old_pass.hexdigest() != item1['passwd']:
            raise HTTPException(status_code=403, detail="Password Anda Salah")
          else:
            q2 = """
              UPDATE akun SET passwd = %s
              WHERE id_karyawan = %s
            """
            # encrypt passwdnya
            new_passwd = hashlib.md5(str(data['new_pass']).encode())
            q2_values = (
              new_passwd.hexdigest(), user['id_karyawan']
            )
            await cursor.execute(q2, q2_values)
            # 3. Klo Sukses, dia bkl save ke db
            await conn.commit()

          return {
            "status": "ok",
            "message": "Sukses Simpan Data"
          }
          

        except aiomysqlerror as e:
          await conn.rollback()
          return JSONResponse(content={"status": "error", "message": f"Database Error {str(e)}"}, status_code=500)
        except HTTPException as e:
          await conn.rollback()
          return JSONResponse(content={"status": "error", "message": f"HTTP Error Error {str(e)}"}, status_code=e.status_code)

  except Exception as e:
    return JSONResponse(content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500)