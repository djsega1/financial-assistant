from aiogram import Router, F
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from states.main import MainStates
from database import create_user

router = Router()


@router.message(CommandStart())
@router.message(F.text == "Назад")
async def start_command(message: Message, state: FSMContext):
    keyboard = ReplyKeyboardBuilder()
    labels = [
        "Счета",
        "Категории",
        "Теги",
        "Транзакции",
        "Бюджеты",
        "Цели",
        "Повторяющиеся",
    ]
    for label in labels:
        keyboard.add(KeyboardButton(text=label))
    keyboard.adjust(3, repeat=3)
    tg_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name or "—"
    create_user(tg_id, username)

    await state.clear()
    text_answer = "Добро пожаловать! Выберите раздел:"
    await state.set_state(MainStates.idle)
    await message.answer(
        text_answer,
        reply_markup=keyboard.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
        parse_mode='HTML',
    )
