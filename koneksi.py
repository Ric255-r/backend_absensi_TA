# import mysql.connector
# pip install mysql-connector-python
# conn = None

import aiomysql

# pip install aiomysql
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import read_db_config


# Initialize connection pool at module level
pool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
  global pool
  config = read_db_config()

  pool = await aiomysql.create_pool(
    host=config["host"],
    user=config["user"],
    password=config["password"],
    db=config["db_name"],
    port=config["port"],
    # minsize=2, # Keep 2 connections always open
    # maxsize=13, # Max 13 connections under load
    # pool_recycle=3600, # Recycle connections every 1h
    minsize=5,
    maxsize=20,
    pool_recycle=3600,
    connect_timeout=10,  # Timeout for establishing new connections
    echo=False,  # Set to True for debugging, False for production
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
