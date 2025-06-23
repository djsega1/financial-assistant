import datetime
from .connection import get_conn, release_conn
from .dbutils import dictfetchall


def report_month(user_id:int, month_str:str)->list:
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
        WITH period AS (
          SELECT to_date(%s,'YYYY-MM') AS start
        ), data AS (
          SELECT
            t.type,
            c.name AS category,
            SUM(t.amount)::numeric(12,2) AS sum_amount
          FROM transactions t
            JOIN accounts a ON t.account_id=a.account_id
            JOIN categories c ON t.category_id=c.category_id
            JOIN period p ON t.occurred_at BETWEEN p.start AND p.start + INTERVAL '1 month'
          WHERE a.user_id=%s
          GROUP BY t.type,c.name
        )
        SELECT * FROM data ORDER BY type, sum_amount DESC
        """, (month_str, user_id))
        return dictfetchall(cur)
    finally:
        cur.close(); release_conn(conn)