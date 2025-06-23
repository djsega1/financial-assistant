import datetime
from aiogram import Router, F, html
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext

from states.main import MainStates
from database import get_account, get_category, report_month, add_transaction, get_transactions
from utils.main import *

router = Router()


@router.message(MainStates.idle, F.text=="Транзакции")
async def idle_tx(message: Message, state: FSMContext):
    await state.set_state(MainStates.idle_transaction)
    kb = ReplyKeyboardBuilder().add(
        KeyboardButton(text="Добавить приход"), KeyboardButton(text="Добавить расход")
    ).add(
        KeyboardButton(text="Мои транзакции"), KeyboardButton(text="Отчёт за месяц")
    ).add(KeyboardButton(text="Назад"))
    kb.adjust(2,2)
    await message.answer("Раздел «Транзакции»", reply_markup=kb.as_markup(resize_keyboard=True))

@router.message(MainStates.idle_transaction, F.text.startswith("Добавить"))
async def add_tx_start(message: Message, state: FSMContext):
    mode = "I" if "приход" in message.text.lower() else "E"
    await state.update_data(tx_type=mode)
    await state.set_state(MainStates.add_transaction)
    await message.answer(
        "Введите: <b>account_id, category_id, amount, описание[, теги через ;]</b>\n"
        "Пример: 1, 3, 500.00, Обед, еда;ресторан",
        parse_mode="HTML"
    )

@router.message(MainStates.add_transaction)
async def add_tx_done(message: Message, state: FSMContext):
    data = await state.get_data()
    tx_type = data.get("tx_type")
    parts = [p.strip() for p in message.text.split(",")]
    if len(parts)<4:
        return await message.answer("❌ Неверный формат. Нужно как минимум 4 поля.")
    try:
        account_id = int(parts[0])
        category_id = int(parts[1])
        amount = float(parts[2])
    except:
        return await message.answer("❌ account_id и category_id — целые, amount — число.")
    description = parts[3]
    tags = []
    if len(parts)>4:
        tags = [t.strip() for t in ",".join(parts[4:]).split(";") if t.strip()]
    uid = message.from_user.id
    # проверки
    if not get_account(uid, account_id):
        return await message.answer(f"❌ Счет #{account_id} не найден.")
    if not get_category(uid, category_id):
        return await message.answer(f"❌ Категория #{category_id} не найдена.")
    tx_id, err = add_transaction(uid, account_id, category_id, amount, tx_type, description, tags)
    if err:
        await message.answer(f"❌ Ошибка: {err}")
    else:
        await state.set_state(MainStates.idle_transaction)
        await message.answer(f"✅ Транзакция #{tx_id} успешно добавлена")

@router.message(MainStates.idle_transaction, F.text=="Мои транзакции")
async def list_tx(message: Message, state: FSMContext):
    uid = message.from_user.id
    rows = get_transactions(uid)
    if not rows:
        return await message.answer("У вас нет транзакций.")
    await message.answer(fmt_transactions(rows), parse_mode="HTML")

@router.message(MainStates.idle_transaction, F.text=="Отчёт за месяц")
async def ask_report_month(message: Message, state: FSMContext):
    await state.set_state(MainStates.wait_report_month)
    await message.answer("Введите месяц <code>YYYY-MM</code> для отчёта:", parse_mode="HTML")

@router.message(MainStates.wait_report_month)
async def report_month_done(message: Message, state: FSMContext):
    txt = message.text.strip()
    try:
        datetime.datetime.strptime(txt, "%Y-%m")
    except:
        return await message.answer("❌ Формат YYYY-MM, например 2025-04. Попробуйте ещё раз.")
    uid = message.from_user.id
    rows = report_month(uid, txt)
    if not rows:
        await message.answer(f"Нет данных за {txt}.")
    else:
        inc = [r for r in rows if r['type']=='I']
        exp = [r for r in rows if r['type']=='E']
        out = [f"<b>📊 Отчёт за {txt}</b>\n"]
        out.append("<b>➕ Приходы:</b>")
        out += [f"{r['category']}: {r['sum_amount']:.2f}" for r in inc] or ["—"]
        out.append("\n<b>➖ Расходы:</b>")
        out += [f"{r['category']}: {r['sum_amount']:.2f}" for r in exp] or ["—"]
        await message.answer("\n".join(out), parse_mode="HTML")
