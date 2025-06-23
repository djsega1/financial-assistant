import asyncio
import logging
import os 

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.base import DefaultKeyBuilder
from redis.asyncio.client import Redis

from database import add_transaction, get_due_recurring, update_recurring_next_run, get_conn, release_conn
from handlers import list_of_routers
from settings.base import BOT_TOKEN

logging.basicConfig(level=logging.INFO)


bot = Bot(token=BOT_TOKEN)
redis_storage = RedisStorage(
    redis=Redis(
        host=os.getenv("REDIS_HOST"),
        port=os.getenv("REDIS_PORT"),
        password=os.getenv("REDIS_PASSWORD"),
        db=2,
    ),
    key_builder=DefaultKeyBuilder(),
)
dp = Dispatcher(storage=redis_storage)


async def recurring_worker(bot: Bot):
    while True:
        due = get_due_recurring()
        if due:
            for r in due:
                uid = r['user_id']
                rid = r['recur_id']
                acc = r['account_id']
                cat = r['category_id']
                amt = float(r['amount'])
                typ = r['type']
                desc= r['description'] or ''
                freq= r['freq_interval']   # psycopg2 возвращает datetime.timedelta
                old_next = r['next_run']
                # вычисляем новый next_run
                try:
                    new_next = old_next + freq
                except Exception:
                    # в случае, если freq_interval – строка '1 month', можно делать UPDATE через SQL:
                    new_next = None

                # пробуем вставить транзакцию
                tx_id, err = add_transaction(uid, acc, cat, amt, typ, desc)
                if err:
                    # оповещаем об ошибке
                    await bot.send_message(
                        uid,
                        f"❌ Не удалось выполнить повтор #{rid} ({old_next})\n"
                        f"Счёт: #{acc}, Категория: #{cat}, Сумма: {amt:.2f}\n"
                        f"Ошибка: {err}"
                    )
                    # не меняем next_run, чтобы попытать ещё раз через час
                else:
                    # если успешно – сдвигаем next_run
                    if new_next:
                        update_recurring_next_run(rid, new_next)
                    else:
                        # если new_next не рассчитали в Python – делаем в БД
                        conn = get_conn(); cur = conn.cursor()
                        cur.execute("""
                            UPDATE recurring_transactions
                            SET next_run = next_run + freq_interval
                            WHERE recur_id=%s
                        """, (rid,))
                        conn.commit(); cur.close(); release_conn(conn)
# оповещаем об успехе
                    await bot.send_message(
                        uid,
                        f"✅ Повтор #{rid} выполнен успешно.\n"
                        f"Создана транзакция #{tx_id}:\n"
                        f"Счёт: #{acc}, Категория: #{cat}, Сумма: {amt:.2f}\n"
                        f"Описание: {desc or '–'}\n"
                        f"Следующий запуск: { (new_next or '(увеличено на interval)') }",
                        parse_mode='HTML'
                    )
        # спим час
        await asyncio.sleep(3600)
        logging.info('worker')


async def main():
    dp.include_routers(*list_of_routers)
    asyncio.create_task(recurring_worker(bot))
    await dp.start_polling(bot)


asyncio.run(main())
