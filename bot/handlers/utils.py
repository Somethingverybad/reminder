from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


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
            InlineKeyboardButton(text="🕔 5 мин", callback_data="time_5"),
            InlineKeyboardButton(text="🕒 15 мин", callback_data="time_15"),
            InlineKeyboardButton(text="🕞 30 мин", callback_data="time_30")
        ],
        [
            InlineKeyboardButton(text="🕐 1 час", callback_data="time_60"),
            InlineKeyboardButton(text="🕕 6 часов", callback_data="time_360")
        ],
        [InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="time_manual")]
    ])


