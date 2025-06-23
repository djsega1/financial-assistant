import datetime
from .connection import get_conn, release_conn
from .dbutils import dictfetchall, dict_fetch_one


def add_goal(user_id:int, name:str, target_amount:float, due_date)->int:
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO goals(user_id,name,target_amount,due_date)
            VALUES(%s,%s,%s,%s)
            RETURNING goal_id
        """, (user_id,name,target_amount,due_date))
        gid = cur.fetchone()[0]
        conn.commit()
        return gid
    finally:
        cur.close(); release_conn(conn)


def get_goals(user_id:int)->list:
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
          SELECT goal_id, name, target_amount, saved_amount, due_date, is_achieved
          FROM goals
          WHERE user_id=%s
          ORDER BY due_date
        """, (user_id,))
        return dictfetchall(cur)
    finally:
        cur.close(); release_conn(conn)

def update_goal_saved(user_id:int, goal_id:int, inc_amount:float)->float:
    """
    Увеличить saved_amount, возвращает новое saved_amount
    """
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
          UPDATE goals
          SET saved_amount = saved_amount + %s
          WHERE goal_id=%s AND user_id=%s
          RETURNING saved_amount
        """, (inc_amount,goal_id,user_id))
        new_val = cur.fetchone()[0]
        conn.commit()
        return new_val
    finally:
        cur.close(); release_conn(conn)

def get_goal(user_id: int, goal_id: int) -> dict | None:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT goal_id, user_id, name, target_amount, saved_amount, due_date, is_achieved
            FROM goals
            WHERE user_id = %s AND goal_id = %s
        """, (user_id, goal_id))
        return dict_fetch_one(cur)
    finally:
        cur.close()
        release_conn(conn)