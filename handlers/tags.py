import aiohttp
from aiogram import Router, F, html
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext

from states.main import MainStates
from database import create_tag, get_tags

router = Router()


@router.message(MainStates.idle, F.text=="Теги")
async def idle_tag(message: Message, state: FSMContext):
    await state.set_state(MainStates.idle_tag)
    kb = ReplyKeyboardBuilder().add(
        KeyboardButton(text="Добавить тег"), KeyboardButton(text="Мои теги")
    ).add(KeyboardButton(text="Назад"))
    kb.adjust(2,1)
    await message.answer("Раздел «Теги»", reply_markup=kb.as_markup(resize_keyboard=True))

@router.message(MainStates.idle_tag, F.text=="Добавить тег")
async def add_tag_start(message: Message, state: FSMContext):
    await state.set_state(MainStates.add_tag)
    await message.answer("Введите название тега:")

@router.message(MainStates.add_tag)
async def add_tag_done(message: Message, state: FSMContext):
    name = message.text.strip()
    uid = message.from_user.id
    tag_id = create_tag(uid, name)
    await state.set_state(MainStates.idle_tag)
    await message.answer(f"✅ Тег создан: #{tag_id} {name}")

@router.message(MainStates.idle_tag, F.text=="Мои теги")
async def list_tags(message: Message, state: FSMContext):
    uid = message.from_user.id
    rows = get_tags(uid)
    if not rows:
        return await message.answer("У вас нет тегов.")
    lines = ["<b>🏷️ Теги:</b>"]
    for r in rows:
        lines.append(f"#{r['tag_id']} {r['name']}")
    await message.answer("\n".join(lines), parse_mode="HTML")