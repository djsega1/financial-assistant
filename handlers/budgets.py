import datetime
from aiogram import Router, F, html
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext

from states.main import MainStates
from utils.main import fmt_budgets
from database import add_budget, get_budgets, get_category

router = Router()

@router.message(MainStates.idle, F.text=="Бюджеты")
async def idle_budget(message: Message, state: FSMContext):
    await state.set_state(MainStates.idle_budget)
    kb = ReplyKeyboardBuilder().add(
        KeyboardButton(text="Добавить бюджет"), KeyboardButton(text="Мои бюджеты")
    ).add(KeyboardButton(text="Назад"))
    kb.adjust(2,1)
    await message.answer("Раздел «Бюджеты»", reply_markup=kb.as_markup(resize_keyboard=True))

@router.message(MainStates.idle_budget, F.text=="Добавить бюджет")
async def add_budget_start(message: Message, state: FSMContext):
    await state.set_state(MainStates.add_budget)
    await message.answer("Введите: category_id, limit, start(YYYY-MM-DD), end(YYYY-MM-DD)")

@router.message(MainStates.add_budget)
async def add_budget_done(message: Message, state: FSMContext):
    parts = [p.strip() for p in message.text.split(",")]
    if len(parts)!=4:
        return await message.answer("❌ Формат: category_id, limit, start, end")
    cid, lim, sd, ed = parts
    try:
        cid = int(cid); lim = float(lim)
        sd = datetime.date.fromisoformat(sd)
        ed = datetime.date.fromisoformat(ed)
    except:
        return await message.answer("❌ Проверьте типы полей.")
    uid = message.from_user.id
    if not get_category(uid, cid):
        return await message.answer(f"❌ Категория #{cid} не найдена.")
    bid = add_budget(uid, cid, lim, sd, ed)
    await state.set_state(MainStates.idle_budget)
    await message.answer(f"✅ Бюджет #{bid} создан.")

@router.message(MainStates.idle_budget, F.text=="Мои бюджеты")
async def list_budgets(message: Message, state: FSMContext):
    uid = message.from_user.id
    rows = get_budgets(uid)
    if not rows:
        return await message.answer("Нет бюджетов.")
    await message.answer(fmt_budgets(rows), parse_mode="HTML")
