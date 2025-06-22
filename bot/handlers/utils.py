from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup,KeyboardButton


def categories_keyboard(categories):
    buttons = []
    for cat in categories:
        buttons.append([
            InlineKeyboardButton(text=cat["name"], callback_data=f"set_category:{cat['id']}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def date_choice_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Сегодня", callback_data="date_today"),
            InlineKeyboardButton(text="📅 Завтра", callback_data="date_tomorrow"),
            InlineKeyboardButton(text="📅 Послезавтра", callback_data="date_dayafter")
        ],
        [InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="date_manual")]
    ])

def time_choice_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🕔 Через 5 мин", callback_data="time_5"),
            InlineKeyboardButton(text="🕔 Через 10 мин", callback_data="time_10"),
            InlineKeyboardButton(text="🕒 Через 15 мин", callback_data="time_15"),
            InlineKeyboardButton(text="🕞 Через 30 мин", callback_data="time_30")
        ],
        [
            InlineKeyboardButton(text="🕐 Через 1 час", callback_data="time_60"),
            InlineKeyboardButton(text="🕕 Через 6 часов", callback_data="time_360")
        ],
        [InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="time_manual")]
    ])


async def show_main_keyboard(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Мои задачи"), KeyboardButton(text="➕ Новая задача")],
            [KeyboardButton(text="🏷 Теги")],
            [KeyboardButton(text="❌ Отмена")]
        ], resize_keyboard=True
    )
    await message.answer("Главное меню:", reply_markup=kb)