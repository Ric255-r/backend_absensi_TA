import asyncio
from datetime import datetime, timedelta
import json
import shutil
from typing import Optional
import uuid
import aiofiles
import aiomysql
from fastapi import APIRouter, BackgroundTasks, Query, Depends, File, Form, Request, HTTPException, Security, UploadFile, WebSocket, WebSocketDisconnect
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
from concurrent.futures import ThreadPoolExecutor

# Create a dedicated thread pool for file operations
FILE_IO_EXECUTOR = ThreadPoolExecutor(max_workers=6)  # Adjust based on your needs

app = APIRouter(
  prefix="/absen"
)

FOTO_CHECKIN = "api/images/foto_checkin"
FOTO_CHECKOUT = "api/images/foto_checkout"

@app.get('/foto_checkin/{filename}')
def get_foto_checkin(filename: str):
  img_path = os.path.join(FOTO_CHECKIN, filename)
  return FileResponse(img_path, media_type='image/png')

@app.get('/foto_checkout/{filename}')
def get_foto_checkout(filename: str):
  img_path = os.path.join(FOTO_CHECKOUT, filename)
  return FileResponse(img_path, media_type='image/png')

# Ini Adalah Lokasi saya, Untuk Uji Coba agar absen saya diapprove
# Maka saya akan mengubah lokasi objek penelitian kepada lokasi saya saat ini
LATITUDE_BENGKOM = -0.0680256
LONGITUDE_BENGKOM = 109.3875546

# # Original Lokasi Bengkel Teknologi Indonesia
# # Jl Gusti Hamzah No 6C Pontianak, Kalimantan Barat
# LATITUDE_BENGKOM = -0.03020289202263597
# LONGITUDE_BENGKOM = 109.3217448800716
@app.get('/get_lokasi_bengkom')
def get_lokasi_bengkom():
  return {
    "latitude_bengkom": LATITUDE_BENGKOM,
    "longitude_bengkom": LONGITUDE_BENGKOM
  }

# Ambil data absensi utk menu utama yang riwayat absen hari ini
@app.get('/my_absen')
async def get_data(
  month: Optional[str] = Query(None),
  year: Optional[str] = Query(None),
  user: JwtAuthorizationCredentials = Security(access_security)
):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:

        try:
          await cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;")

          if not month and not year:
            q1 = "SELECT * FROM absensi WHERE DATE(tanggal_absen) = DATE(CURRENT_TIMESTAMP()) and id_karyawan = %s"
            await cursor.execute(q1, user['id_karyawan'])

            # Return dalam bentuk dict
            items = await cursor.fetchone()
          else:
            q1 = """
              SELECT a.*, pa.keterangan, pa.foto_lampiran FROM absensi a
              LEFT JOIN pengajuan_absen pa 
                ON a.id_karyawan = pa.id_karyawan
                  AND DATE(a.tanggal_absen) BETWEEN pa.tanggal_mulai AND pa.tanggal_akhir
              WHERE MONTH(a.tanggal_absen) = %s and YEAR(a.tanggal_absen) = %s and a.id_karyawan = %s ORDER BY DATE(a.tanggal_absen) ASC
            """
            await cursor.execute(q1, (month, year, user['id_karyawan']) )

            # Return dalam bentuk list
            items = await cursor.fetchall()

          return items
        except aiomysqlerror as e:
          return JSONResponse(content={"status": "error", "message": f"Database Error {str(e)}"}, status_code=500)
        except HTTPException as e:
          return JSONResponse(content={"status": "error", "message": f"HTTP Error Error {str(e)}"}, status_code=e.status_code)

  except Exception as e:
    return JSONResponse(content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500)

# Utk Validasi button checkin, klo exists tolak.
@app.get('/check_in')
async def get_data_checkin(
  user: JwtAuthorizationCredentials = Security(access_security)
):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:

        try:
          await cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;")

          # Returnnya Integer
          q1 = """
            SELECT 
              EXISTS(
                SELECT 1 FROM absensi a WHERE a.id_karyawan = %s and DATE(a.check_in) = CURDATE()
              ) AS has_checkin,
              EXISTS(
                SELECT 1 FROM pengajuan_absen pa WHERE pa.id_karyawan = %s 
                  AND CURDATE() BETWEEN pa.tanggal_mulai AND pa.tanggal_akhir
              ) AS in_pengajuan
          """
          await cursor.execute(q1, (user['id_karyawan'], user['id_karyawan']))
          items1 = await cursor.fetchone()

          # Jika Data ada, tolak krn udh checkin hari ini
          if bool(items1['has_checkin']) or bool(items1['in_pengajuan']):
            return JSONResponse(content={"status": "error", "message": f"Anda Sudah Checkin"}, status_code=403)
          
          return JSONResponse(content={"status": "ok", "message": f"Belum Ada Checkin"}, status_code=200)
        

        except aiomysqlerror as e:
          return JSONResponse(content={"status": "error", "message": f"Database Error {str(e)}"}, status_code=500)
        except HTTPException as e:
          return JSONResponse(content={"status": "error", "message": f"HTTP Error Error {str(e)}"}, status_code=e.status_code)

      
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500)
  
# Utk Validasi button checkout, klo exists tolak.
@app.get('/check_out')
async def get_data_checkout(
  user: JwtAuthorizationCredentials = Security(access_security)
):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:

        try:
          await cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;")

          # q1 = "SELECT 1 FROM absensi WHERE id_karyawan = %s and DATE(check_out) = DATE(CURRENT_TIMESTAMP())"
          # await cursor.execute(q1, user['id_karyawan'])

          # Returnnya Integer
          q1 = """
            SELECT 
              EXISTS(
                SELECT 1 FROM absensi a WHERE a.id_karyawan = %s AND DATE(a.check_out) = CURDATE()
              ) AS has_check_out,
              EXISTS(
                SELECT 1 FROM pengajuan_absen pa WHERE pa.id_karyawan = %s 
                AND CURDATE() BETWEEN pa.tanggal_mulai and pa.tanggal_akhir
              ) AS has_pengajuan
          """
          await cursor.execute(q1, (user['id_karyawan'], user['id_karyawan']))

          items = await cursor.fetchone()

          # Jika Data ada, tolak krn udh checkout hari ini
          if bool(items['has_check_out']) or bool(items['has_pengajuan']):
            return JSONResponse(content={"status": "error", "message": f"Anda Sudah CheckOut"}, status_code=403)
          
          return JSONResponse(content={"status": "ok", "message": f"Belum Ada Checkout"}, status_code=200)

        except aiomysqlerror as e:
          return JSONResponse(content={"status": "error", "message": f"Database Error {str(e)}"}, status_code=500)
        except HTTPException as e:
          return JSONResponse(content={"status": "error", "message": f"HTTP Error Error {str(e)}"}, status_code=e.status_code)

      
  except Exception as e:
    return JSONResponse(content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500)

def day_to_indo(day):
  hari = ""
  if day == "Monday":
    hari = "Senin"
  elif day == "Tuesday":
    hari = "Selasa"
  elif day == "Wednesday":
    hari = "Rabu"
  elif day == "Thursday":
    hari = "Kamis"
  elif day == "Friday":
    hari = "Jumat"
  elif day == "Saturday":
    hari = "Sabtu"
  else:
    hari = "Minggu"
  return hari

def convert_timedelta_str(time):
  # konversi 8:00:00 ke 08:00:00
  total_seconds = int(time.total_seconds())
  hours, remainder = divmod(total_seconds, 3600)
  minutes, seconds = divmod(remainder, 60)
  
  jam_formatted_str = f'{hours:02}:{minutes:02}:{seconds:02}'
  return jam_formatted_str

# Helper function to get config. It uses its OWN connection.
async def _get_lateness_tolerance(pool: aiomysql.Pool):
  async with pool.acquire() as conn:
    async with conn.cursor(aiomysql.DictCursor) as cursor:
      await cursor.execute("SELECT toleransi_terlambat FROM konfigurasi_aplikasi")
      return await cursor.fetchone()
            
# Helper function to get the day name in Indonesian.
async def _get_indonesian_day_name(pool: aiomysql.Pool):
  async with pool.acquire() as conn:
    async with conn.cursor(aiomysql.DictCursor) as cursor:
      await cursor.execute("SET @@lc_time_names = 'id_ID';")
      await cursor.execute("SELECT DAYNAME(DATE(NOW())) as hari_ini;")
      return await cursor.fetchone()
    
# Helper function to get schedule info. It uses its OWN connection.
async def _get_schedule_and_time(pool: aiomysql.Pool, day_name: str):
  async with pool.acquire() as conn:
    async with conn.cursor(aiomysql.DictCursor) as cursor:
      q = "SELECT shift_mulai, TIME(NOW()) as jam_skrg FROM jadwal_kerja WHERE hari_dalam_seminggu = %s"
      await cursor.execute(q, (day_name,))
      return await cursor.fetchone()


def save_upload_file(upload: UploadFile, dest: str):
  with open(dest, "wb") as f:
    shutil.copyfileobj(upload.file, f)   # stream, no read() besar ke memori

  print("Sukses Simpan Gambar")

# Store Data Checkin
@app.post('/check_in')
async def absen_hadir(
  request: Request,
  background_task: BackgroundTasks,
  user: JwtAuthorizationCredentials = Security(access_security),
):
  print("Eksekusi Fungsi Check In")
  try:
    pool = await get_db()

    # --- Step 1: Perform independent READ operations in parallel ---
    # These tasks run concurrently, each on its own database connection.
    # fn_hari = _get_indonesian_day_name(pool)
    # fn_config = _get_lateness_tolerance(pool)
    
    # We await them together. The total wait time is the time of the LONGEST query.
    day_item, config_item = await asyncio.gather(
      _get_indonesian_day_name(pool),
      _get_lateness_tolerance(pool)
    )
    
    if not day_item or not config_item:
      return JSONResponse(content={"status": "error", "message": "Failed to fetch initial data (day or config)."}, status_code=500)

    # Now get the schedule, which depends on the day name
    schedule_item = await _get_schedule_and_time(pool, day_item['hari_ini'])
    
    if not schedule_item:
      return JSONResponse(content={"status": "error", "message": "Work schedule for today not found."}, status_code=404)

    # get form data
    data = await request.form()
    #read foto_checkin. jangan make read. lemot
    # content = await data['foto_checkin'].read()
    # Generate Filename tapi blm di store ke disk
    filename = f"{uuid.uuid4()}.jpg"
    file_location = os.path.join(FOTO_CHECKIN, filename)

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          # 1. Start Transaction
          await conn.begin()

          q1 = """
            INSERT INTO absensi (
              id_karyawan, tanggal_absen, check_in, 
              latitude_checkin, longitude_checkin, foto_checkin
            )
            VALUES(%s, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP(), %s, %s, %s)
          """
          q1_values = (
            user['id_karyawan'], data['latitude_checkin'], data['longitude_checkin'], filename
          )
          await cursor.execute(q1, q1_values)

          # fetch data jam skrg, ini msh bentuk time atau timedelta.
          # timedelta(hours=3) akan menjadi 3:00:00.
          # timedelta(hours=15) akan menjadi 15:00:00.
          jam_skrg_timedelta = schedule_item['jam_skrg']  
          jadwal_checkin_timedelta = schedule_item['shift_mulai'] #Ini Jg. Jadi jam 8:00:00.

          # ak jdkan function convert timedelta ke formattedstr
          jam_skrg_str = convert_timedelta_str(jam_skrg_timedelta)
          jadwal_checkin_formatted_str = convert_timedelta_str(jadwal_checkin_timedelta)
          # print(f"Isi jam skrg str: {jam_skrg_str}") # 10:15:00. 
          # print(f"Isi jadwal checkin: {jadwal_checkin_formatted_str}") # 08:00:00

          # menit toleransi berbentuk int menit.
          menit_toleransi = config_item['toleransi_terlambat']
          # Ubah ke bentuk datetime, tapi isi strptime harus string di argumen 1
          format_waktu = "%H:%M:%S"
          waktu_checkin_sekarang = datetime.strptime(jam_skrg_str, format_waktu)
          jadwal_checkin = datetime.strptime(jadwal_checkin_formatted_str, format_waktu)

          # hitung batas waktu toleransi
          batas_waktu_checkin = jadwal_checkin + timedelta(minutes=menit_toleransi)

          # Bandingkan waktu check-in asli dengan waktu terakhir yang diizinkan
          # Jika waktu check-in lebih lambat dari batas waktu, mereka telat.
          if waktu_checkin_sekarang > batas_waktu_checkin:
            is_telat = 1
            print(f"Karyawan telat. Check-in: {waktu_checkin_sekarang.time()}, Batas Waktu: {batas_waktu_checkin.time()}")
          else:
            is_telat = 0
            print(f"Karyawan tepat waktu. Check-in: {waktu_checkin_sekarang.time()}, Batas Waktu: {batas_waktu_checkin.time()}")

          q4 = """
            UPDATE absensi
            SET is_telat = %s
            WHERE id_karyawan = %s AND DATE(tanggal_absen) = DATE(CURRENT_TIMESTAMP())
          """
          await cursor.execute(q4, (is_telat, user['id_karyawan']))

          # 3. Klo Sukses, dia bkl save ke db
          await conn.commit()

          # Select Utk Websocket
          await cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;")
          q5 = "SELECT * FROM karyawan WHERE id_karyawan = %s"
          await cursor.execute(q5, user['id_karyawan'])
          items5 = await cursor.fetchone()

          for ws_con in absensi_connection:
            await ws_con.send_text(
              json.dumps({
                "message": f"Check in baru dari {items5['nama_karyawan']}",
                "data": serialize_data(items5)
              })
            )
          
          # Sistem Fire and Forget. klo begini proses dari route /check_in ga terhambat krna write file
          # async def _save_file_bg():
          #   try:
          #     # Write Filenya
          #     loop = asyncio.get_event_loop()
          #     await loop.run_in_executor(
          #       FILE_IO_EXECUTOR,
          #       lambda: open(file_location, 'wb').write(content)
          #     )
          #     # async with aiofiles.open(file_location, 'wb') as f:
          #     #   await f.write(content)
          #     print("Sukses Simpan File")
          #   except Exception as e:
          #     print(f"Gagal Simpan File di BG: {str(e)}")

          # # Pakai asyncio utk run di bg
          # asyncio.create_task(_save_file_bg())
          background_task.add_task(save_upload_file, data['foto_checkin'], file_location)
            
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
  
# # Store Data Checkin Original
# @app.post('/check_in')
# async def absen_hadir(
#   request: Request,
#   user: JwtAuthorizationCredentials = Security(access_security),
# ):
#   print("Eksekusi Fungsi Check In")
  
#   # return JSONResponse(content={"status": "error", "message": f"Isi data user {user['id_karyawan']}"}, status_code=500)
#   try:
#     pool = await get_db()

#     async with pool.acquire() as conn:
#       async with conn.cursor(aiomysql.DictCursor) as cursor:

#         try:
#           # 1. Start Transaction
#           await conn.begin()

#           # set harian local ke indo
#           try:
#               await cursor.execute("SET @@lc_time_names = 'id_ID';")
#               print("Locale set to id_ID successfully.")
#           except Exception as e:
#               print(f"Failed to set locale to id_ID: {e}")

#           # get hari indo
#           qHari = "SELECT DAYNAME(DATE(NOW())) as hari_ini;"
#           await cursor.execute(qHari)
#           item_hari = await cursor.fetchone()

#           if item_hari is None:
#             return JSONResponse(content={"status": "error", "message": "Error Fetch harian. lokale ? "}, status_code=500)

#           # print(f"Fetched day name: {item_hari['hari_ini']}")


#           # 2. Execute querynya
#           data = await request.form()
#           q1 = """
#             INSERT INTO absensi (
#               id_karyawan, tanggal_absen, check_in, 
#               latitude_checkin, longitude_checkin, foto_checkin
#             )
#             VALUES(%s, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP(), %s, %s, %s)
#           """

#           filename = f"{uuid.uuid4()}.png"
#           file_location = os.path.join(FOTO_CHECKIN, filename)

#           #saveFile
#           content = await data['foto_checkin'].read()
#           async with aiofiles.open(file_location, 'wb') as f:
#             await f.write(content)

#           q1_values = (
#             user['id_karyawan'], data['latitude_checkin'], data['longitude_checkin'], filename
#           )
#           await cursor.execute(q1, q1_values)

#           # Utk Penetapan dia telat atau nda, ambil jadwal ditabel skrg sama time now
#           q2 = "SELECT *, TIME(NOW()) as jam_skrg FROM jadwal_kerja WHERE hari_dalam_seminggu = %s"
#           await cursor.execute(q2, item_hari['hari_ini'])
#           schedule_item = await cursor.fetchone()

#           # fetch data jam skrg, ini msh bentuk time atau timedelta.
#           # timedelta(hours=3) akan menjadi 3:00:00.
#           # timedelta(hours=15) akan menjadi 15:00:00.
#           jam_skrg_timedelta = schedule_item['jam_skrg']  
#           jadwal_checkin_timedelta = schedule_item['shift_mulai'] #Ini Jg. Jadi jam 8:00:00.

#           # ak jdkan function convert timedelta ke formattedstr
#           jam_skrg_str = convert_timedelta_str(jam_skrg_timedelta)
#           jadwal_checkin_formatted_str = convert_timedelta_str(jadwal_checkin_timedelta)

#           # print(f"Isi jam skrg str: {jam_skrg_str}") # 10:15:00. 
#           # print(f"Isi jadwal checkin: {jadwal_checkin_formatted_str}") # 08:00:00

#           q3 = "SELECT toleransi_terlambat FROM konfigurasi_aplikasi"
#           await cursor.execute(q3)
#           item3 = await cursor.fetchone()
#           # ambil nilai value toleransi yg udh integer
#           menit_toleransi = item3['toleransi_terlambat']

#           # Ubah ke bentuk datetime, tapi isi strptime harus string di argumen 1
#           format_waktu = "%H:%M:%S"
#           waktu_checkin_sekarang = datetime.strptime(jam_skrg_str, format_waktu)
#           jadwal_checkin = datetime.strptime(jadwal_checkin_formatted_str, format_waktu)

#           # hitung batas waktu toleransi
#           batas_waktu_checkin = jadwal_checkin + timedelta(minutes=menit_toleransi)

#           # Bandingkan waktu check-in asli dengan waktu terakhir yang diizinkan
#           # Jika waktu check-in lebih lambat dari batas waktu, mereka telat.
#           if waktu_checkin_sekarang > batas_waktu_checkin:
#             is_telat = 1
#             print(f"Karyawan telat. Check-in: {waktu_checkin_sekarang.time()}, Batas Waktu: {batas_waktu_checkin.time()}")
#           else:
#             is_telat = 0
#             print(f"Karyawan tepat waktu. Check-in: {waktu_checkin_sekarang.time()}, Batas Waktu: {batas_waktu_checkin.time()}")

#           q4 = """
#             UPDATE absensi
#             SET is_telat = %s
#             WHERE id_karyawan = %s AND DATE(tanggal_absen) = DATE(CURRENT_TIMESTAMP())
#           """
#           await cursor.execute(q4, (is_telat, user['id_karyawan']))

#           # 3. Klo Sukses, dia bkl save ke db
#           await conn.commit()

#           # Select Utk Websocket
#           await cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;")
#           q5 = "SELECT * FROM karyawan WHERE id_karyawan = %s"
#           await cursor.execute(q5, user['id_karyawan'])
#           items5 = await cursor.fetchone()

#           for ws_con in absensi_connection:
#             await ws_con.send_text(
#               json.dumps({
#                 "message": f"Check in baru dari {items5['nama_karyawan']}",
#                 "data": serialize_data(items5)
#               })
#             )
#           return {
#             "status": "ok",
#             "message": "Sukses Simpan Data"
#           }
          

#         except aiomysqlerror as e:
#           await conn.rollback()
#           return JSONResponse(content={"status": "error", "message": f"Database Error {str(e)}"}, status_code=500)
#         except HTTPException as e:
#           await conn.rollback()
#           return JSONResponse(content={"status": "error", "message": f"HTTP Error Error {str(e)}"}, status_code=e.status_code)

#   except Exception as e:
#     return JSONResponse(content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500)
  


# Update data checkout
@app.put('/check_out')
async def check_out(
  request: Request,
  background_task: BackgroundTasks,
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

          filename = f"{uuid.uuid4()}.jpg"
          file_location = os.path.join(FOTO_CHECKOUT, filename)

          #saveFile. Jangan Make Read. Bikin Lambat
          # content = await data['foto_checkout'].read()

          q1 = """
            UPDATE absensi SET check_out = CURRENT_TIMESTAMP(), latitude_checkout = %s, longitude_checkout = %s,
            foto_checkout = %s WHERE DATE(tanggal_absen) = DATE(CURRENT_TIMESTAMP()) and id_karyawan = %s
          """
          q1_values = (
            data['latitude_checkout'], data['longitude_checkout'],
            filename, user['id_karyawan']
          )
          await cursor.execute(q1, q1_values)
          # 3. Klo Sukses, dia bkl save ke db
          await conn.commit()

          # Select Utk Websocket
          await cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;")
          q2 = "SELECT * FROM karyawan WHERE id_karyawan = %s"
          await cursor.execute(q2, user['id_karyawan'])
          items2 = await cursor.fetchone()

          for ws_con in absensi_connection:
            await ws_con.send_text(
              json.dumps({
                "message": f"Absen checkout baru dari {items2['nama_karyawan']}",
                "data": serialize_data(items2)
              })
            )

          # Concurrent
          # Sistem Fire and Forget. klo begini proses dari route /check_oyt ga terhambat krna write file
          # async def _save_file_bg():
          #   try:
          #     # Write Filenya
          #     loop = asyncio.get_event_loop()
          #     await loop.run_in_executor(
          #       FILE_IO_EXECUTOR,
          #       lambda: open(file_location, 'wb').write(content)
          #     )
          #     # async with aiofiles.open(file_location, 'wb') as f:
          #     #   await f.write(content)
          #     print("Sukses Simpan File")
          #   except Exception as e:
          #     print(f"Gagal Simpan File di BG: {str(e)}")

          # # Pakai asyncio utk run di bg
          # asyncio.create_task(_save_file_bg())

          background_task.add_task(save_upload_file, data['foto_checkout'], file_location)

          return {
            "status": "ok",
            "message": "Sukses Update Data Absensi"
          }
          

        except aiomysqlerror as e:
          await conn.rollback()
          return JSONResponse(content={"status": "error", "message": f"Database Error {str(e)}"}, status_code=500)
        except HTTPException as e:
          await conn.rollback()
          return JSONResponse(content={"status": "error", "message": f"HTTP Error Error {str(e)}"}, status_code=e.status_code)

  except Exception as e:
    return JSONResponse(content={"status": "error", "message": f"Koneksi Error {str(e)}"}, status_code=500)