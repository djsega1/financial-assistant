import datetime
from .connection import get_conn, release_conn
from .dbutils import dictfetchall, dict_fetch_one


def create_category(user_id:int, name:str, parent_id:int=None)->int:
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO categories(user_id,name,parent_category_id)
            VALUES(%s,%s,%s)
            RETURNING category_id
        """, (user_id,name,parent_id))
        cid = cur.fetchone()[0]
        conn.commit()
        return cid
    finally:
        cur.close(); release_conn(conn)


def get_categories(user_id:int)->list:
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            SELECT category_id, name, parent_category_id
            FROM categories
            WHERE user_id=%s
            ORDER BY parent_category_id NULLS FIRST, category_id
        """, (user_id,))
        return dictfetchall(cur)
    finally:
        cur.close(); release_conn(conn)


def get_category(user_id: int, category_id: int) -> dict | None:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT category_id, user_id, name, parent_category_id
            FROM categories
            WHERE user_id = %s AND category_id = %s
        """, (user_id, category_id))
        return dict_fetch_one(cur)
    finally:
        cur.close()
        release_conn(conn)
