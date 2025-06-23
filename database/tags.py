import datetime
from .connection import get_conn, release_conn
from .dbutils import dictfetchall, dict_fetch_one


def create_tag(user_id:int, name:str)->int:
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO tags(user_id,name)
            VALUES(%s,%s)
            ON CONFLICT(user_id,name) DO UPDATE SET name=EXCLUDED.name
            RETURNING tag_id
        """, (user_id,name))
        tag_id = cur.fetchone()[0]
        conn.commit()
        return tag_id
    finally:
        cur.close(); release_conn(conn)


def get_tags(user_id:int)->list:
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            SELECT tag_id, name
            FROM tags
            WHERE user_id=%s
            ORDER BY name
        """, (user_id,))
        return dictfetchall(cur)
    finally:
        cur.close(); release_conn(conn)


def get_tag(user_id: int, tag_id: int) -> dict | None:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT tag_id, user_id, name
            FROM tags
            WHERE user_id = %s AND tag_id = %s
        """, (user_id, tag_id))
        return dict_fetch_one(cur)
    finally:
        cur.close()
        release_conn(conn)