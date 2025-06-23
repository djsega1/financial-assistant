import datetime
from .connection import get_conn, release_conn
from .dbutils import dictfetchall, dict_fetch_one


def create_account(user_id:int, name:str, currency:str, balance:float=0)->int:
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO accounts(user_id,name,currency,current_balance)
            VALUES(%s,%s,%s,%s)
            RETURNING account_id
        """, (user_id,name,currency,balance))
        account_id = cur.fetchone()[0]
        conn.commit()
        return account_id
    finally:
        cur.close(); release_conn(conn)


def get_accounts(user_id:int)->list:
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            SELECT account_id, name, currency, current_balance
            FROM accounts
            WHERE user_id=%s
            ORDER BY account_id
        """, (user_id,))
        return dictfetchall(cur)
    finally:
        cur.close(); release_conn(conn)


def get_account(user_id: int, account_id: int) -> dict | None:
    """
    Возвращает одну запись из accounts по user_id и account_id
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT account_id, user_id, name, currency, current_balance
            FROM accounts
            WHERE user_id = %s AND account_id = %s
        """, (user_id, account_id))
        return dict_fetch_one(cur)
    finally:
        cur.close()
        release_conn(conn)
