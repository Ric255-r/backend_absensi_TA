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

app = APIRouter(
  prefix="/admin"
)



@app.put('/update_karyawan')
async def update_karyawan(
  request: Request
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
          q1 = """
            UPDATE karyawan SET nama_karyawan = %s, email_karyawan = %s, nomor_hp = %s, tanggal_rekrut = %s,
            status = %s, id_departemen = %s, posisi = %s
            WHERE id_karyawan = %s
          """
          q1_values = (
            data['nama_karyawan'], data['email_karyawan'], data['nomor_hp'], 
            data['tanggal_rekrut'], data['status'], data['id_departemen'], data['posisi'], data['id_karyawan']
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
  
@app.put('/update_akun')
async def update_akun(
  request: Request
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
          q1 = """
            UPDATE akun SET passwd = %s, roles = %s, id_karyawan = %s, status = %s 
            WHERE username = %s
          """
          passwd = hashlib.md5(str(data['passwd']).encode())
          q1_values = (
            passwd.hexdigest(), data['roles'],
            data['id_karyawan'], data['status'],
            data['username'] 
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
  

@app.put('/update_konfigurasi')
async def update_konfigurasi(
  request: Request
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
          q1 = """
            UPDATE konfigurasi_aplikasi SET toleransi_terlambat = %s, maks_hari_cuti = %s
            WHERE id_pengaturan = %s
          """
          q1_values = (
            data['toleransi_terlambat'], data['maks_hari_cuti'], data['id_pengaturan']
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
  
@app.put('/update_jadwal/{id_jadwal}')
async def update_konfigurasi(
  id_jadwal: str,
  request: Request
):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:

        try:
          # 1. Start Transaction
          await conn.begin()

          # 2. Execute querynya
          key_field = ""
          data = await request.json()
          if "shift_mulai" in data:
            key_field = "shift_mulai"
          else:
            key_field = "shift_selesai"
          
          isi_waktu = data[key_field]


          print(f"Isi Data {data}")


          q1 = f"""
            UPDATE jadwal_kerja SET {key_field} = %s where id_jadwal = %s 
          """
          q1_values = (
            isi_waktu, id_jadwal 
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