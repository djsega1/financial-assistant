
import os
from psycopg2 import pool


USER = os.getenv("POSTGRES_USER")
PASSWORD = os.getenv("POSTGRES_PASSWORD")
HOST = os.getenv("POSTGRES_HOST")
# HOST = "localhost"
PORT = os.getenv("POSTGRES_PORT")
DATABASE = os.getenv("POSTGRES_DB")
DATABASE_URL = f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"

_pg_pool = pool.SimpleConnectionPool(
    1,
    20,
    host=HOST,
    user=USER,
    password=PASSWORD,
    database=DATABASE,
    port=PORT,
)


def get_conn():
    return _pg_pool.getconn()


def release_conn(conn):
    _pg_pool.putconn(conn)


x = _pg_pool.getconn()
_pg_pool.putconn(x)