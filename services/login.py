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

# Untuk Routingnya jadi http://192.xx.xx.xx:5500/api
app = APIRouter()

@app.post('/login')
async def login(
  request: Request
):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:

        try:
          
          await cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;")

          data = await request.json()
          # Jadikan md5
          req_passwd = hashlib.md5(str(data['passwd']).encode())

          query = """
            SELECT a.* FROM akun a
            WHERE a.username = %s
          """
          await cursor.execute(query, data['username'])
          items = await cursor.fetchone()

          #Jika g ad data
          if not items:
            raise HTTPException(status_code=404, detail="User Not Found")

          # ambil passwd
          stored_pass = items['passwd'].strip()

          # bandingkan md5 dari form dengan passwd md5 yg udh terstore
          if req_passwd.hexdigest() != stored_pass:
            raise HTTPException(status_code=401, detail="Password Salah")
          
          access_token = access_security.create_access_token(serialize_data(items))
          refresh_token = refresh_security.create_refresh_token(serialize_data(items))

          query = """
            SELECT a.* FROM akun a
            WHERE a.username = %s
          """
          await cursor.execute(query, data['username'])
          items = await cursor.fetchone()

          await conn.begin()
          query2 = """
            UPDATE akun SET last_login = CURRENT_TIMESTAMP() WHERE username = %s
          """
          await cursor.execute(query2, data['username'])
          await conn.commit()

          return {
            "data_user": serialize_data(items),
            "access_token" : access_token,
            "refresh_token" : refresh_token,
          }

        except aiomysqlerror as e:
          await conn.rollback()
          return JSONResponse(content={"status": "error", "message": f"Database Error {str(e)}"}, status_code=500)
        except HTTPException as e:
          await conn.rollback()
          return JSONResponse(content={"status": "error", "message": f"HTTP Error Error {str(e)}"}, status_code=e.status_code)
    
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500)

@app.get('/user')
async def user(
  user: JwtAuthorizationCredentials = Security(access_security)
):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:

        try:
          await cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;")

          q1 = "SELECT a.*, k.nama_karyawan, k.foto_profile FROM akun a INNER JOIN karyawan k ON a.id_karyawan = k.id_karyawan WHERE a.id_karyawan = %s"
          await cursor.execute(q1, (user['id_karyawan'], ))

          # Return dalam bentuk list
          items = await cursor.fetchone()

          return items
        except aiomysqlerror as e:
          return JSONResponse(content={"status": "error", "message": f"Database Error {str(e)}"}, status_code=500)
        except HTTPException as e:
          return JSONResponse(content={"status": "error", "message": f"HTTP Error Error {str(e)}"}, status_code=e.status_code)

  except Exception as e:
    return JSONResponse(content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500)

