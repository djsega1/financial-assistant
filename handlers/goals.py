import datetime
from aiogram import Router, F, html
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext

from states.main import MainStates
from utils.main import fmt_goals
from database import add_goal, get_goals, update_goal_saved, get_goal

router = Router()


@router.message(MainStates.idle, F.text=="Цели")
async def idle_goals(message: Message, state: FSMContext):
    await state.set_state(MainStates.idle_goal)
    kb = ReplyKeyboardBuilder().add(
        KeyboardButton(text="Добавить цель"), KeyboardButton(text="Мои цели")
    ).add(KeyboardButton(text="Пополнить цель"), KeyboardButton(text="Назад"))
    kb.adjust(2,2)
    await message.answer("Раздел «Цели»", reply_markup=kb.as_markup(resize_keyboard=True))

@router.message(MainStates.idle_goal, F.text=="Добавить цель")
async def add_goal_start(message: Message, state: FSMContext):
    await state.set_state(MainStates.add_goal)
    await message.answer("Введите: name, target_amount, due_date(YYYY-MM-DD)")

@router.message(MainStates.add_goal)
async def add_goal_done(message: Message, state: FSMContext):
    parts = [p.strip() for p in message.text.split(",")]
    if len(parts)!=3:
        return await message.answer("❌ Формат: name, amount, due_date")
    name = parts[0]
    try:
        tgt = float(parts[1])
        due = datetime.date.fromisoformat(parts[2])
    except:
        return await message.answer("❌ Проверьте поля.")
    uid = message.from_user.id
    gid = add_goal(uid, name, tgt, due)
    await state.set_state(MainStates.idle_goal)
    await message.answer(f"✅ Цель #{gid} «{name}» создана.")

@router.message(MainStates.idle_goal, F.text=="Мои цели")
async def list_goals(message: Message, state: FSMContext):
    uid = message.from_user.id
    rows = get_goals(uid)
    if not rows:
        return await message.answer("Нет целей.")
    await message.answer(fmt_goals(rows), parse_mode="HTML")

@router.message(MainStates.idle_goal, F.text=="Пополнить цель")
async def refill_goal_start(message: Message, state: FSMContext):
    await state.set_state(MainStates.refill_goal)
    await message.answer("Введите: goal_id, amount\nПример: 2, 5000")

@router.message(MainStates.refill_goal)
async def refill_goal_done(message: Message, state: FSMContext):
    parts = [p.strip() for p in message.text.split(",")]
    if len(parts)!=2:
        return await message.answer("❌ Формат: goal_id, amount")
    try:
        gid = int(parts[0]); inc = float(parts[1])
    except:
        return await message.answer("❌ Проверьте типы.")
    uid = message.from_user.id
    if not get_goal(uid, gid):
        return await message.answer(f"❌ Цель #{gid} не найдена.")
    new = update_goal_saved(uid, gid, inc)
    await state.set_state(MainStates.idle_goal)
    await message.answer(f"✅ Цель #{gid} пополнена. Всего накоплено: {new:.2f}")