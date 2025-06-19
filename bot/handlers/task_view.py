import logging
from datetime import datetime
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from states import Form
from services.django_api import get_tasks, update_task, get_categories
from aiogram.utils.text_decorations import html_decoration as html
from handlers.main_menu import show_main_keyboard

logger = logging.getLogger(__name__)
router = Router()

@router.message(lambda message: message.text == "📋 Мои задачи")
async def ask_category_filter(message: types.Message, state: FSMContext):
    categories = await get_categories(user_id=message.from_user.id)
    buttons = [[InlineKeyboardButton(text="📋 Все задачи", callback_data="filter_cat:all")]]
    for cat in categories:
        buttons.append([InlineKeyboardButton(text=cat["name"], callback_data=f"filter_cat:{cat['id']}")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выберите категорию задач:", reply_markup=kb)
    await state.set_state(Form.task_category_filter)

@router.callback_query(Form.task_category_filter, lambda c: c.data.startswith("filter_cat:"))
async def filter_tasks_by_category(callback: CallbackQuery, state: FSMContext):
    category_id = callback.data.split(":")[1]
    if category_id == "all":
        category_id = None
    else:
        await state.update_data(filter_category=category_id)

    tasks = await get_tasks(callback.from_user.id, category=category_id)
    if not tasks:
        await callback.message.answer("У вас пока нет задач.")
    else:
        for task in tasks:
            task_id = task["id"]
            title = html.quote(task["title"])
            description = html.quote(task["description"] or "")
            due_date = datetime.fromisoformat(task["due_date"]).strftime("%d.%m.%Y %H:%M")
            category_name = task.get("category", {}).get("name", "Без тега")
            text = (
                f"<b>{title}</b>\n🕓 <i>{due_date}</i>\n\n"
                f"Описание:\n {description}\n\n"
                f"Тег: <i>{category_name}</i>"
            )
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=f"✅ Выполнить - {title}", callback_data=f"done:{task_id}")]
                ]
            )
            await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    categories = await get_categories(user_id=callback.from_user.id)
    buttons = [[InlineKeyboardButton(text="📋 Все задачи", callback_data="filter_cat:all")]]
    for cat in categories:
        buttons.append([InlineKeyboardButton(text=cat["name"], callback_data=f"filter_cat:{cat['id']}")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("Выберите категорию задач:", reply_markup=kb)
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("done:"))
async def mark_task_done(callback: CallbackQuery):
    task_id = callback.data.split(":")[1]
    success = await update_task(task_id, {"is_done": True})
    if success:
        await callback.message.edit_text("✅ Задача отмечена как выполненная.")
    else:
        await callback.message.answer("❌ Не удалось обновить задачу.")
    await callback.answer()