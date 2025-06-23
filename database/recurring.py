import datetime
from .connection import get_conn, release_conn
from .dbutils import dictfetchall, dict_fetch_one


def add_recurring(
    user_id:int,
    account_id:int,
    category_id:int,
    amount:float,
    freq_interval:str,  # например '1 month'
    tx_type:str,        # 'I' или 'E'
    description:str=''
)->int:
    conn = get_conn(); cur = conn.cursor()
    try:
        # next_run по умолчанию сегодня
        today = datetime.date.today()
        cur.execute(f"""
            INSERT INTO recurring_transactions
              (user_id,account_id,category_id,amount,type,freq_interval,next_run,description)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING recur_id
        """, (user_id,account_id,category_id,amount,tx_type,freq_interval,today,description))
        rid = cur.fetchone()[0]
        conn.commit()
        return rid
    finally:
        cur.close(); release_conn(conn)


def get_recurring(user_id:int)->list:
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
          SELECT recur_id, account_id, category_id, amount, type, freq_interval, next_run, description
          FROM recurring_transactions
          WHERE user_id=%s
          ORDER BY next_run
        """, (user_id,))
        return dictfetchall(cur)
    finally:
        cur.close(); release_conn(conn)


def get_recurring_one(user_id: int, recur_id: int) -> dict | None:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT
              recur_id, user_id, account_id, category_id,
              amount, type, freq_interval, next_run, description
            FROM recurring_transactions
            WHERE user_id = %s AND recur_id = %s
        """, (user_id, recur_id))
        return dict_fetch_one(cur)
    finally:
        cur.close()
        release_conn(conn)


def run_due_recurring():
    """
    Создаёт транзакции для всех повторов с next_run<=today
    и сдвигает next_run += freq_interval.
    """
    conn = get_conn(); cur = conn.cursor()
    try:
        today = datetime.date.today()
        cur.execute("""
          SELECT recur_id, account_id, category_id, amount, type, freq_interval, next_run, description
          FROM recurring_transactions
          WHERE next_run <= %s
        """, (today,))
        rows = cur.fetchall()
        for (rid, acc, cat, amt, tt, freq, nr, desc) in rows:
            # вставляем транзакцию
            cur.execute("""
              INSERT INTO transactions(account_id,category_id,amount,type,occurred_at,description)
              VALUES(%s,%s,%s,%s,%s,%s)
            """, (acc, cat, amt, tt, nr, desc))
            # сдвигаем next_run
            cur.execute("""
              UPDATE recurring_transactions
              SET next_run = next_run + %s
              WHERE recur_id=%s
            """, (freq, rid))
        conn.commit()
    finally:
        cur.close(); release_conn(conn)


def get_due_recurring() -> list[dict]:
    """
    Берём все повторы, у которых next_run <= сегодня
    """
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            SELECT
              recur_id, user_id, account_id, category_id,
              amount, type, freq_interval, next_run, description
            FROM recurring_transactions
            WHERE next_run <= CURRENT_DATE
            ORDER BY user_id, next_run
        """)
        return dictfetchall(cur)
    finally:
        cur.close(); release_conn(conn)


def update_recurring_next_run(recur_id: int, next_run: datetime.date) -> None:
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE recurring_transactions
            SET next_run = %s
            WHERE recur_id = %s
        """, (next_run, recur_id))
        conn.commit()
    finally:
        cur.close(); release_conn(conn)