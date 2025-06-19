import logging
from datetime import datetime, timedelta, date
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from services.django_api import get_tasks, create_task, update_task
from states import Form
from handlers.utils import date_choice_keyboard, time_choice_keyboard, categories_keyboard
from handlers.simple_dialog import router
from aiogram.utils.text_decorations import html_decoration as html

logger = logging.getLogger(__name__)

@router.message(lambda message: message.text == "📋 Мои задачи")
async def show_user_tasks(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category_id = data.get("filter_category")

    tasks = await get_tasks(message.from_user.id, category=category_id)

    if not tasks:
        await message.answer("У вас пока нет задач.")
        return

    for task in tasks:
        task_id = task["id"]
        title = html.quote(task["title"])
        description = html.quote(task["description"] or "")
        due_date = datetime.fromisoformat(task["due_date"]).strftime("%d.%m.%Y %H:%M")
        category_name = task.get("category", {}).get("name", "Без тега")

        text = (f"<b>{title}</b>\n🕓 <i>{due_date}</i>\n\nОписание:\n {description}\n\n"
                f"Тег: <i>{category_name}</i>")
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"✅ Выполнить - {title}", callback_data=f"done:{task_id}")]
            ]
        )
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@router.message(lambda message: message.text == "➕ Новая задача")
async def start_new_task(message: types.Message, state: FSMContext):
    await state.set_state(Form.task_title)
    await message.answer("Введите заголовок задачи:",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="❌ Отмена")]],
                             resize_keyboard=True))

@router.message(Form.task_title)
async def process_task_title(message: types.Message, state: FSMContext):
    await state.update_data(task_title=message.text)
    await state.set_state(Form.task_description)
    await message.answer("Введите описание задачи:")

@router.message(Form.task_description)
async def process_task_description(message: types.Message, state: FSMContext):
    await state.update_data(task_description=message.text)
    await state.set_state(Form.task_due_date)
    await message.answer("Выберите дату задачи:",
                         reply_markup=date_choice_keyboard())

@router.callback_query(Form.task_due_date, lambda c: c.data.startswith("date_"))
async def process_task_date(callback: CallbackQuery, state: FSMContext):
    today = date.today()
    value = callback.data.split("_")[1]

    if value == "today":
        selected = today
    elif value == "tomorrow":
        selected = today + timedelta(days=1)
    elif value == "dayafter":
        selected = today + timedelta(days=2)
    elif value == "manual":
        await callback.message.answer("Введите дату в формате ДД.ММ.ГГГГ:")
        return

    await state.update_data(task_due_date=str(selected))
    await state.set_state(Form.task_due_time)
    await callback.message.answer("Выберите время выполнения:",
                                  reply_markup=time_choice_keyboard())
    await callback.answer()

@router.message(Form.task_due_date)
async def process_manual_date(message: types.Message, state: FSMContext):
    try:
        due_date = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
        await state.update_data(task_due_date=str(due_date))
        await state.set_state(Form.task_due_time)
        await message.answer("Теперь выберите время выполнения:",
                             reply_markup=time_choice_keyboard())
    except ValueError:
        await message.answer("❌ Неверный формат. Введите ДД.ММ.ГГГГ")

@router.callback_query(Form.task_due_time, lambda c: c.data.startswith("time_"))
async def process_task_time(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split("_")[1]

    if value == "manual":
        await callback.message.answer("Введите время в формате ЧЧ:ММ:")
        return

    try:
        minutes = int(value)
        due_dt = datetime.now() + timedelta(minutes=minutes)
        await state.update_data(task_due_time=due_dt.strftime("%H:%M"))
        await finalize_task_creation(callback.from_user.id, state, callback.message)
    except Exception as e:
        logger.error(f"Time selection error: {e}")
        await callback.message.answer("Ошибка выбора времени")
    finally:
        await callback.answer()

@router.message(Form.task_due_time)
async def process_manual_time(message: types.Message, state: FSMContext):
    try:
        datetime.strptime(message.text.strip(), "%H:%M")
        await state.update_data(task_due_time=message.text.strip())
        await finalize_task_creation(message.from_user.id, state, message)
    except ValueError:
        await message.answer("❌ Неверный формат. Введите ЧЧ:ММ")

async def finalize_task_creation(user_id: int, state: FSMContext, message_or_cbmsg: types.Message):
    data = await state.get_data()

    try:
        due_time = datetime.strptime(data["task_due_time"], "%H:%M").time()
        due_date = datetime.strptime(data["task_due_date"], "%Y-%m-%d").date()
        due_datetime = datetime.combine(due_date, due_time)

        response = await create_task(
            user_id=user_id,
            title=data["task_title"],
            description=data["task_description"],
            due_date=due_datetime.isoformat(),
            reminder_intervals=[],
            remind_daily=False
        )

        if response.get("id"):
            await message_or_cbmsg.answer("✅ Задача успешно создана!")

            categories = await get_categories()
            if categories:
                await message_or_cbmsg.answer(
                    "Выберите категорию:",
                    reply_markup=categories_keyboard(categories)
                )
                await state.update_data(task_id=response["id"])
                await state.set_state(Form.task_category)
                return
        else:
            await message_or_cbmsg.answer("❌ Ошибка при создании задачи")

    except Exception as e:
        logger.error(f"Task finalization error: {e}")
        await message_or_cbmsg.answer("❌ Ошибка создания задачи")

    await state.clear()
    await show_main_keyboard(message_or_cbmsg)

@router.callback_query(Form.task_category, lambda c: c.data.startswith("set_category:"))
async def process_task_category(callback: CallbackQuery, state: FSMContext):
    category_id = callback.data.split(":")[1]
    data = await state.get_data()

    if await update_task(data["task_id"], {"category": category_id}):
        await callback.message.answer("✅ Категория сохранена")
    else:
        await callback.message.answer("❌ Ошибка сохранения категории")

    await callback.answer()
    await state.clear()
    await show_main_keyboard(callback.message)

@router.callback_query(lambda c: c.data.startswith("done:"))
async def mark_task_done(callback: CallbackQuery):
    task_id = callback.data.split(":")[1]

    success = await update_task(task_id, {"is_done": True})

    if success:
        await callback.message.edit_text("✅ Задача отмечена как выполненная.")
    else:
        await callback.message.answer("❌ Не удалось обновить задачу.")

    await callback.answer()
