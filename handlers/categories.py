import aiohttp
from aiogram import Router, F, html
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext

from states.main import MainStates
from database import create_category, get_category, get_categories

router = Router()


@router.message(MainStates.idle, F.text=="Категории")
async def idle_category(message: Message, state: FSMContext):
    await state.set_state(MainStates.idle_category)
    kb = ReplyKeyboardBuilder().add(
        KeyboardButton(text="Добавить категорию"), KeyboardButton(text="Мои категории")
    ).add(KeyboardButton(text="Назад"))
    kb.adjust(2,1)
    await message.answer("Раздел «Категории»", reply_markup=kb.as_markup(resize_keyboard=True))

@router.message(MainStates.idle_category, F.text=="Добавить категорию")
async def add_category_start(message: Message, state: FSMContext):
    await state.set_state(MainStates.add_category)
    await message.answer(
        "Введите: <b>имя</b> или <b>имя, parent_id</b>\n"
        "Пример: Продукты или Развлечения, 3",
        parse_mode="HTML"
    )

@router.message(MainStates.add_category)
async def add_category_done(message: Message, state: FSMContext):
    parts = [p.strip() for p in message.text.split(",")]
    name = parts[0]
    parent = int(parts[1]) if len(parts)>1 and parts[1].isdigit() else None
    uid = message.from_user.id
    # проверка родителя
    if parent:
        if not get_category(uid, parent):
            return await message.answer(f"❌ Категория #{parent} не найдена.")
    cat_id = create_category(uid, name, parent)
    await state.set_state(MainStates.idle_category)
    await message.answer(f"✅ Категория создана: #{cat_id} {name}")


@router.message(MainStates.idle_category, F.text=="Мои категории")
async def list_categories(message: Message, state: FSMContext):
    uid = message.from_user.id
    rows = get_categories(uid)
    if not rows:
        return await message.answer("У вас ещё нет категорий.")
    lines = ["<b>📂 Категории:</b>"]
    for r in rows:
        pid = r['parent_category_id']
        lines.append(f"#{r['category_id']} {r['name']}" + (f" (дочернее от #{pid})" if pid else ""))
    await message.answer("\n".join(lines), parse_mode="HTML")