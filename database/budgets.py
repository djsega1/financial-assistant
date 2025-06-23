import datetime
from .connection import get_conn, release_conn
from .dbutils import dictfetchall, dict_fetch_one


def add_budget(user_id:int, category_id:int, amount_limit:float, start_date, end_date)->int:
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO budgets(user_id,category_id,amount_limit,start_date,end_date)
            VALUES(%s,%s,%s,%s,%s)
            RETURNING budget_id
        """, (user_id,category_id,amount_limit,start_date,end_date))
        bid = cur.fetchone()[0]
        conn.commit()
        return bid
    finally:
        cur.close(); release_conn(conn)


def get_budgets(user_id:int)->list:
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
          SELECT
            b.budget_id, c.name AS category, b.amount_limit,
            b.start_date, b.end_date,
            COALESCE(SUM(t.amount),0) AS spent
          FROM budgets b
            JOIN categories c ON b.category_id=c.category_id
            LEFT JOIN transactions t
              ON t.category_id=b.category_id
              AND t.type='E'
              AND t.occurred_at::date BETWEEN b.start_date AND b.end_date
          WHERE b.user_id=%s
          GROUP BY b.budget_id,c.name,b.amount_limit,b.start_date,b.end_date
          ORDER BY b.start_date DESC
        """, (user_id,))
        return dictfetchall(cur)
    finally:
        cur.close(); release_conn(conn)


def get_budget(user_id: int, budget_id: int) -> dict | None:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT
              b.budget_id,
              b.user_id,
              b.category_id,
              c.name       AS category_name,
              b.amount_limit,
              b.start_date,
              b.end_date
            FROM budgets b
            JOIN categories c ON b.category_id = c.category_id
            WHERE b.user_id = %s AND b.budget_id = %s
        """, (user_id, budget_id))
        bud = dict_fetch_one(cur)
        if not bud:
            return None
        # считаем потрачено
        cur.execute("""
            SELECT COALESCE(SUM(amount),0)
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.user_id = %s
              AND t.type = 'E'
              AND t.category_id = %s
              AND t.occurred_at::date BETWEEN %s AND %s
        """, (user_id, bud['category_id'], bud['start_date'], bud['end_date']))
        spent = cur.fetchone()[0]
        bud['spent'] = float(spent)
        return bud
    finally:
        cur.close()
        release_conn(conn)