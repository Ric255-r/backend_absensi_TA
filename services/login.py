import aiomysql
from fastapi import APIRouter, Request, HTTPException, Security
from fastapi.responses import JSONResponse
from koneksi import get_db
from fastapi_jwt import JwtAuthorizationCredentials
from aiomysql import Error as aiomysqlerror
from jwt_auth import access_security, refresh_security
import hashlib
from utils.fn_conv_str import serialize_data

# Untuk Routingnya jadi http://192.xx.xx.xx:5500/api
app = APIRouter()


@app.post("/login")
async def login(request: Request):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          await conn.begin()
          await cursor.execute(
            "SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;"
          )

          payload = await request.json()
          # Jadikan md5
          req_passwd = hashlib.md5(str(payload["passwd"]).encode())

          query = """
            SELECT a.* FROM akun a
            WHERE a.username = %s
          """
          await cursor.execute(query, payload["username"])
          items = await cursor.fetchone()

          if "is_admin" in payload:
            if payload["is_admin"] == 1 and items["roles"] not in ["admin", "owner"]:
              raise HTTPException(status_code=401, detail="Akses Anda Dibatasi")

          # Jika g ad payload
          if not items:
            raise HTTPException(status_code=404, detail="User Not Found")

          # Binding Device Id
          stored_device_id = items["device_id"]
          is_first_time_bind = False

          if not stored_device_id:
            # Masukkan Ke Hasil Response dari payload
            items["device_id"] = payload["device_id"]
            is_first_time_bind = True

          elif payload["device_id"] != stored_device_id:
            raise HTTPException(
              status_code=401, detail="Device Anda Berbeda. Akses Dibatasi"
            )

          # ambil passwd
          stored_pass = items["passwd"].strip()

          # bandingkan md5 dari form dengan passwd md5 yg udh terstore
          if req_passwd.hexdigest() != stored_pass:
            raise HTTPException(status_code=401, detail="Password Salah")

          # Mainkan Untuk Di Lempar Ke Token
          items["is_first_time_bind"] = is_first_time_bind

          access_token = access_security.create_access_token(serialize_data(items))
          refresh_token = refresh_security.create_refresh_token(serialize_data(items))

          # HANYA commit jika ini BUKAN binding pertama
          if not is_first_time_bind:
            query2 = (
              "UPDATE akun SET last_login = CURRENT_TIMESTAMP() WHERE username = %s"
            )
            await cursor.execute(query2, payload["username"])
            await conn.commit()
          else:
            # Jika ini binding pertama, batalkan (karena kita tidak melakukan UPDATE)
            await conn.rollback()

          return {
            "data_user": serialize_data(items),
            "access_token": access_token,
            "refresh_token": refresh_token,
          }

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


@app.get("/user")
async def user(user: JwtAuthorizationCredentials = Security(access_security)):
  try:
    pool = await get_db()

    async with pool.acquire() as conn:
      async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
          await cursor.execute(
            "SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;"
          )

          # Jika g ad data
          if not user:
            raise HTTPException(status_code=404, detail="User Not Found")

          q1 = "SELECT a.*, k.nama_karyawan, k.foto_profile FROM akun a INNER JOIN karyawan k ON a.id_karyawan = k.id_karyawan WHERE a.id_karyawan = %s"
          await cursor.execute(q1, (user["id_karyawan"],))
          # Return dalam bentuk list
          items = await cursor.fetchone()

          if not items:
            raise HTTPException(status_code=404, detail="User Not Found in DB")

          # --- ✨ VALIDASI DEVICE BINDING SAAT STARTUP ✨ ---
          # Ambil device_id dari token yang dikirim
          device_id_from_token = user["device_id"]

          # Ambil device_id dari database
          device_id_from_db = items.get("device_id")

          # Bandingkan!
          if device_id_from_db != device_id_from_token:
            # Ini adalah skenario Anda:
            # DB (A002) tidak cocok dengan Token (A001).
            # Paksa user login ulang.
            raise HTTPException(
              status_code=401, detail="Device binding berubah. Silakan login kembali."
            )
          # --- SELESAI VALIDASI ---

          return items  # Jika cocok, kembalikan data user
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


@app.put("/confirm-bind")
async def confirm_bind(
  user: JwtAuthorizationCredentials = Security(access_security),
):  # WAJIB AMAN
  try:
    # 'user' adalah payload dari token
    username = user["username"]
    device_id_from_token = user["device_id"]

    if not username or not device_id_from_token:
      raise HTTPException(status_code=401, detail="Token tidak valid")

    pool = await get_db()
    async with pool.acquire() as conn:
      async with conn.cursor() as cursor:
        try:
          await conn.begin()
          # Update DB HANYA JIKA user & device_id di DB masih NULL
          query = """
            UPDATE akun 
            SET device_id = %s, last_login = CURRENT_TIMESTAMP() 
            WHERE username = %s AND device_id IS NULL
          """
          await cursor.execute(query, (device_id_from_token, username))

          if cursor.rowcount == 0:
            # Gagal update, mungkin sudah di-bind di device lain
            await conn.rollback()
            raise HTTPException(status_code=409, detail="Akun sudah ter-bind.")

          await conn.commit()
          return {"status": "ok", "message": "Device berhasil di-bind"}

        except Exception as e:
          await conn.rollback()
          raise HTTPException(status_code=500, detail=str(e))

  except Exception as e:
    detail = getattr(e, "detail", str(e))
    status_code = getattr(e, "status_code", 401)
    return JSONResponse(
      content={"status": "error", "message": detail}, status_code=status_code
    )
