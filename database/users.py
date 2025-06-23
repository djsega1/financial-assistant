import datetime
from .connection import get_conn, release_conn
from .dbutils import dictfetchall


def create_user(user_id: int, username: str) -> None:
    """
    Создаёт нового пользователя или обновляет username, если он уже есть в БД.
    user_id здесь совпадает с Telegram user_id.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO users(user_id, username)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE
              SET username = EXCLUDED.username
        """, (user_id, username))
        conn.commit()
    finally:
        cur.close()
        release_conn(conn)

# def get_user(user_id: int) -> dict | None:
#     """
#     Возвращает запись пользователя или None, если его нет.
#     """
#     conn = get_conn()
#     cur = conn.cursor()
#     try:
#         cur.execute("""
#             SELECT user_id, username, joined_at
#             FROM users
#             WHERE user_id = %s
#         """, (user_id,))
#         return dict_fetch_one(cur)
#     finally:
#         cur.close()
#         release_conn(conn)