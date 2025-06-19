from aiogram import types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup

from services.django_api import register_user_api, get_categories
from aiogram.utils.text_decorations import html_decoration as html
from states import Form
from handlers.utils import show_main_keyboard  # Вынесем функцию сюда
from handlers.simple_dialog import router


@router.message(Command("start", "menu"))
@router.message(lambda message: message.text.lower() in ["меню", "главное меню"])
async def show_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    success = await register_user_api(message.from_user)
    if success:
        await show_main_keyboard(message)
    else:
        await message.answer("Ошибка регистрации. Попробуйте позже.", reply_markup=ReplyKeyboardRemove())



@router.message(lambda message: message.text == "🏷 Теги")
async def show_user_categories(message: types.Message):
    categories = await get_categories(user_id=message.from_user.id)
    if not categories:
        await message.answer("У вас пока нет тегов.")
        return

    kb = InlineKeyboardMarkup(row_width=1)
    for cat in categories:
        kb.insert(InlineKeyboardButton(text=cat["name"], callback_data=f"edit_cat:{cat['id']}"))

    kb.add(InlineKeyboardButton(text="➕ Создать новый тег", callback_data="create_cat"))
    await message.answer("Ваши теги:", reply_markup=kb)
