import logging
from aiogram import Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from services.django_api import register_user_api
from handlers.utils import date_choice_keyboard, time_choice_keyboard, categories_keyboard

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start", "menu"))
@router.message(lambda message: message.text.lower() in ["меню", "главное меню"])
async def show_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    success = await register_user_api(message.from_user)
    if success:
        await show_main_keyboard(message)
    else:
        await message.answer("Ошибка регистрации. Попробуйте позже.", reply_markup=ReplyKeyboardRemove())

async def show_main_keyboard(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Мои задачи"), KeyboardButton(text="➕ Новая задача")],
            [KeyboardButton(text="🏷 Теги")],
            [KeyboardButton(text="❌ Отмена")]
        ], resize_keyboard=True
    )
    await message.answer("Главное меню:", reply_markup=kb)