# import mysql.connector
# pip install mysql-connector-python
# conn = None

import aiomysql # Utk Avoid Race Condition
# import os
# var = os.getenv('passwd_platinum')

# pip install aiomysql
from contextlib import asynccontextmanager

from fastapi import FastAPI

# Baca file koneksi_config.txt
def read_config(filename):
  with open(filename, 'r') as file:
    line = file.readline().strip() # Baca baris pertama dan remove leading/trailing whitespace
    if line:
      parts = line.split(",")
      if len(parts) == 4: #cek klo yg udh d split mmg isinya 4
        return tuple(part.strip() for part in parts)
      else:
        print(f"Error: Incorrect number of elements in the line. Expected 4, found {len(parts)}.")
        return None

# Initialize connection pool at module level
pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
  global pool
  result = read_config('koneksi_config.txt')

  if result:
    db_name, host, user, port = result

    pool = await aiomysql.create_pool(
      host=host,
      user=user,
      # password=str(var),
      db=db_name,
      port=int(port),
      # minsize=2, # Keep 2 connections always open
      # maxsize=13, # Max 13 connections under load
      # pool_recycle=3600, # Recycle connections every 1h
      minsize=5,
      maxsize=20,
      pool_recycle=3600,
      connect_timeout=10, # Timeout for establishing new connections
      echo=False, # Set to True for debugging, False for production
    )
    
    """
      Rumus Connect Timeout
      Small files (<10MB)	10 (default)	Safe for most APIs.
      Medium files (10-100MB)	30	Prevents rare timeouts on slow networks.
      Large files (>100MB)	60	Only needed for very slow connections.
    """

    print("Database connection pool created")

    yield
    # shutdown, close pool
    if pool:
      try:
        pool.close()
        await pool.wait_closed()
        print("Database Pool Ditutup")
      except Exception as e:
        print(f"Error closing database pool: {e}")


async def get_db():
  return pool