import datetime

import psycopg2
from psycopg2 import errors
from .connection import get_conn, release_conn
from .dbutils import dictfetchall, dict_fetch_one


def add_transaction(
    user_id:int,
    account_id:int,
    category_id:int,
    amount:float,
    tx_type:str,            # 'I' или 'E'
    description:str='',
    tag_names:list=None
)->int:
    tag_names = tag_names or []
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO transactions(account_id,category_id,amount,type,description)
            VALUES(%s,%s,%s,%s,%s)
            RETURNING transaction_id
        """, (account_id, category_id, amount, tx_type, description))
        tx_id = cur.fetchone()[0]
        # привяжем теги
        for name in tag_names:
            cur.execute("""
                INSERT INTO tags(user_id,name)
                VALUES(%s,%s)
                ON CONFLICT(user_id,name) DO UPDATE SET name=EXCLUDED.name
                RETURNING tag_id
            """, (user_id,name))
            tag_id = cur.fetchone()[0]
            cur.execute("""
                INSERT INTO transaction_tags(transaction_id, tag_id)
                VALUES(%s,%s)
                ON CONFLICT DO NOTHING
            """, (tx_id, tag_id))
        conn.commit()
        return tx_id, None
    except psycopg2.Error as e:
        conn.rollback()
        if isinstance(e, errors.RaiseException):
            errmsg = e.diag.message_primary
        else:
            errmsg = str(e).splitlines()[0]
        return None, errmsg
    finally:
        cur.close(); release_conn(conn)


def get_transactions(user_id:int, limit:int=50, from_date=None, to_date=None)->list:
    conn = get_conn(); cur = conn.cursor()
    try:
        sql = """
          SELECT
            t.transaction_id, t.amount, t.type, t.occurred_at, t.description,
            a.name AS account, c.name AS category,
            COALESCE(string_agg(g.name,','), '') AS tags
          FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            JOIN categories c ON t.category_id = c.category_id
            LEFT JOIN transaction_tags tt ON tt.transaction_id = t.transaction_id
            LEFT JOIN tags g ON g.tag_id = tt.tag_id
          WHERE a.user_id = %s
        """
        params = [user_id]
        if from_date:
            sql += " AND t.occurred_at >= %s"; params.append(from_date)
        if to_date:
            sql += " AND t.occurred_at <= %s"; params.append(to_date)
        sql += " GROUP BY t.transaction_id,a.name,c.name ORDER BY t.occurred_at DESC LIMIT %s"
        params.append(limit)
        cur.execute(sql, tuple(params))
        return dictfetchall(cur)
    finally:
        cur.close(); release_conn(conn)


def delete_transaction(user_id:int, tx_id:int)->bool:
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
          DELETE FROM transactions
          WHERE transaction_id=%s
            AND account_id IN (SELECT account_id FROM accounts WHERE user_id=%s)
        """, (tx_id, user_id))
        cnt = cur.rowcount
        conn.commit()
        return cnt>0
    finally:
        cur.close(); release_conn(conn)


def get_transaction(user_id: int, transaction_id: int) -> dict | None:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT
                t.transaction_id,
                t.account_id,
                a.name    AS account_name,
                t.category_id,
                c.name    AS category_name,
                t.amount,
                t.type,
                t.occurred_at,
                t.description
            FROM transactions t
            JOIN accounts a  ON t.account_id  = a.account_id
            LEFT JOIN categories c ON t.category_id = c.category_id
            WHERE a.user_id = %s AND t.transaction_id = %s
        """, (user_id, transaction_id))
        tx = dict_fetch_one(cur)
        if not tx:
            return None
        # подтянем теги
        cur.execute("""
            SELECT g.name
            FROM transaction_tags tt
            JOIN tags g ON tt.tag_id = g.tag_id
            WHERE tt.transaction_id = %s
        """, (transaction_id,))
        tags = [r[0] for r in cur.fetchall()]
        tx['tags'] = tags
        return tx
    finally:
        cur.close()
        release_conn(conn)