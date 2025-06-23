import datetime
from aiogram import Router, F, html
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext

from states.main import MainStates
from utils.main import fmt_recurring
from database import add_recurring, get_recurring, run_due_recurring, get_account, get_category

router = Router()

@router.message(MainStates.idle, F.text=="Повторяющиеся")
async def idle_rec(message: Message, state: FSMContext):
    await state.set_state(MainStates.idle_recurring)
    kb = ReplyKeyboardBuilder().add(
        KeyboardButton(text="Добавить повтор"), KeyboardButton(text="Мои повторы")
    ).add(KeyboardButton(text="Запустить повторы"), KeyboardButton(text="Назад"))
    kb.adjust(2,2)
    await message.answer("Раздел «Повторяющиеся»", reply_markup=kb.as_markup(resize_keyboard=True))

@router.message(MainStates.idle_recurring, F.text=="Добавить повтор")
async def add_rec_start(message: Message, state: FSMContext):
    await state.set_state(MainStates.add_recurring)
    await message.answer(
        "Введите: acc_id, cat_id, amount, type(I/E), freq_interval, description\n"
        "Пример: 1, 3, 1000, E, 1 month, Коммуналка"
    )

@router.message(MainStates.add_recurring)
async def add_rec_done(message: Message, state: FSMContext):
    parts = [p.strip() for p in message.text.split(",")]
    if len(parts)<6:
        return await message.answer("❌ Формат: acc_id, cat_id, amount, type, freq_interval, desc")
    try:
        acc, cat = int(parts[0]), int(parts[1])
        amt = float(parts[2]); tt = parts[3]
        freq = parts[4]; desc = ",".join(parts[5:])
    except:
        return await message.answer("❌ Проверьте поля.")
    uid = message.from_user.id
    if not get_account(uid, acc):
        return await message.answer(f"❌ Счет #{acc} не найден.")
    if not get_category(uid, cat):
        return await message.answer(f"❌ Категория #{cat} не найдена.")
    rid = add_recurring(uid, acc, cat, amt, freq, tt, desc)
    await state.set_state(MainStates.idle_recurring)
    await message.answer(f"✅ Повтор #{rid} создан.")

@router.message(MainStates.idle_recurring, F.text=="Мои повторы")
async def list_rec(message: Message, state: FSMContext):
    uid = message.from_user.id
    rows = get_recurring(uid)
    if not rows:
        return await message.answer("Нет повторов.")
    await message.answer(fmt_recurring(rows), parse_mode="HTML")

@router.message(MainStates.idle_recurring, F.text=="Запустить повторы")
async def run_rec(message: Message, state: FSMContext):
    run_due_recurring()
    await message.answer("✅ Все запланированные повторы выполнены.")