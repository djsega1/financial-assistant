import aiohttp
from aiogram import Router, F, html
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext

from states.main import MainStates
from database import create_account, get_accounts
from utils.main import fmt_accounts

router = Router()


@router.message(MainStates.idle, F.text=="Счета")
async def idle_account(message: Message, state: FSMContext):
    await state.set_state(MainStates.idle_account)
    kb = ReplyKeyboardBuilder().add(
        KeyboardButton(text="Добавить счет"), KeyboardButton(text="Мои счета")
    ).add(KeyboardButton(text="Назад"))
    kb.adjust(2,1)
    await message.answer("Раздел «Счета»", reply_markup=kb.as_markup(resize_keyboard=True))

@router.message(MainStates.idle_account, F.text=="Добавить счет")
async def add_account_start(message: Message, state: FSMContext):
    await state.set_state(MainStates.add_account)
    await message.answer(
        "Введите: <b>название, валюта, начальный баланс</b> через запятую.\n"
        "Пример: Основной, RUB, 1000.00",
        parse_mode="HTML"
    )

@router.message(MainStates.add_account)
async def add_account_done(message: Message, state: FSMContext):
    parts = [p.strip() for p in message.text.split(",")]
    if len(parts)!=3:
        return await message.answer("❌ Формат: название, валюта, баланс. Попробуйте снова.")
    name, cur_code, bal_text = parts
    try:
        bal = float(bal_text)
    except:
        return await message.answer("❌ Баланс должен быть числом.")
    uid = message.from_user.id
    acct_id = create_account(uid, name, cur_code, bal)
    await state.set_state(MainStates.idle_account)
    await message.answer(
        f"✅ Счет создан:\n"
        f"#{acct_id} <b>{name}</b> [{cur_code}] — {bal:.2f}",
        parse_mode="HTML"
    )

@router.message(MainStates.idle_account, F.text=="Мои счета")
async def list_accounts(message: Message, state: FSMContext):
    uid = message.from_user.id
    rows = get_accounts(uid)
    if not rows:
        return await message.answer("У вас ещё нет счетов.")
    await message.answer(fmt_accounts(rows), parse_mode="HTML")