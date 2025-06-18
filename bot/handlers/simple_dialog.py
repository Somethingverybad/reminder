import logging
from datetime import datetime, timedelta, date

import aiohttp
from aiogram import Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from services.api import *
from states import Form
from handlers.utils import *
from services.api import get_categories

logger = logging.getLogger(__name__)
router = Router()



# 🔹 Команды
@router.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    success = await register_user_api(message.from_user)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Мои задачи", callback_data="get_tasks")],
        [InlineKeyboardButton(text="➕ Новая задача", callback_data="new_task")],
    ])
    if success:
        await message.answer("Привет! Ты успешно зарегистрирован. Выберите действие:", reply_markup=kb)
    else:
        await message.answer("Привет! Но регистрация не удалась. Попробуйте позже.")
    await state.clear()

@router.message(Command("newtask"))
async def start_new_task(message: types.Message, state: FSMContext):
    await state.set_state(Form.task_title)
    await message.answer("Введите заголовок задачи:")

# 🔹 Создание задачи поэтапно
@router.message(Form.task_title)
async def task_title_input(message: types.Message, state: FSMContext):
    await state.update_data(task_title=message.text)
    await state.set_state(Form.task_description)
    await message.answer("Введите описание задачи:")

@router.message(Form.task_description)
async def task_description_input(message: types.Message, state: FSMContext):
    await state.update_data(task_description=message.text)
    await state.set_state(Form.task_due_date)
    await message.answer("Выберите дату задачи или введите вручную:", reply_markup=date_choice_keyboard())

@router.message(Form.task_due_date)
async def task_due_date_input(message: types.Message, state: FSMContext):
    try:
        due_date = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
        await state.update_data(task_due_date=str(due_date))
        await state.set_state(Form.task_due_time)
        await message.answer("Теперь выберите время задачи:", reply_markup=time_choice_keyboard())
    except ValueError:
        await message.answer("❌ Неверный формат даты. Введите в формате ДД.ММ.ГГГГ.")

@router.callback_query(lambda c: c.data and c.data.startswith("date_"))
async def date_choice_handler(callback: CallbackQuery, state: FSMContext):
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
        await state.set_state(Form.task_due_date)
        await callback.answer()
        return
    else:
        await callback.answer("Неизвестная дата.")
        return

    await state.update_data(task_due_date=str(selected))
    await state.set_state(Form.task_due_time)
    await callback.message.answer("Теперь выберите время задачи:", reply_markup=time_choice_keyboard())
    await callback.answer()

async def finalize_task_creation(user_id: int, state: FSMContext, message_or_cbmsg: types.Message):
    data = await state.get_data()
    try:
        due_time = datetime.strptime(data["task_due_time"], "%H:%M").time()
        due_date = datetime.strptime(data["task_due_date"], "%Y-%m-%d")
        due_datetime = datetime.combine(due_date, due_time)

        response = await create_task(
            user_id=user_id,
            title=data["task_title"],
            description=data["task_description"],
            due_date=due_datetime.isoformat()
        )

        if response.get("id"):
            await state.update_data(task_id=response["id"])
            categories = await get_categories()
            if categories:
                kb = categories_keyboard(categories)
                await message_or_cbmsg.answer(
                    f"✅ Задача создана: {data['task_title']}\n"
                    f"📅 На {due_datetime.strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"Выберите категорию для задачи:",
                    reply_markup=kb
                )
                await state.set_state(Form.task_category)
            else:
                await message_or_cbmsg.answer("✅ Задача создана, но категории недоступны.")
                await state.clear()
        else:
            await message_or_cbmsg.answer(f"Ошибка при создании задачи: {response}")
            await state.clear()
    except Exception as e:
        logger.warning(f"❌ Ошибка создания задачи: {e}")
        await message_or_cbmsg.answer("❌ Произошла ошибка при создании задачи.")
        await state.clear()

@router.callback_query(lambda c: c.data and c.data.startswith("time_"))
async def time_choice_handler(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split("_")[1]
    if value == "manual":
        await callback.message.answer("Введите время в формате ЧЧ:ММ:")
        await state.set_state(Form.task_due_time)
        await callback.answer()
        return
    try:
        minutes = int(value)
        now = datetime.now()
        due_dt = now + timedelta(minutes=minutes)
        await state.update_data(task_due_date=str(due_dt.date()))
        await state.update_data(task_due_time=due_dt.strftime("%H:%M"))
        await callback.message.answer(f"⏰ Время выбрано: {due_dt.strftime('%H:%M')}")
        await finalize_task_creation(callback.from_user.id, state, callback.message)
    except Exception as e:
        logger.warning(f"Ошибка выбора времени: {e}")
        await callback.message.answer("Ошибка при выборе времени.")

@router.message(Form.task_due_time)
async def task_due_time_input(message: types.Message, state: FSMContext):
    try:
        input_time = message.text.strip()
        logger.info(f"⏰ Введено время: '{input_time}'")

        due_time = datetime.strptime(input_time, "%H:%M").time()
        logger.info(f"✅ Распознанное время: {due_time}")

        data = await state.get_data()
        logger.info(f"📦 Данные из FSM: {data}")

        due_date = datetime.strptime(data["task_due_date"], "%Y-%m-%d")
        due_datetime = datetime.combine(due_date, due_time)
        logger.info(f"📆 Итоговая дата и время: {due_datetime}")

        user_id = message.from_user.id
        response = await create_task(
            user_id=user_id,
            title=data["task_title"],
            description=data["task_description"],
            due_date=due_datetime.isoformat()
        )
        logger.info(f"📤 Ответ от API: {response}")

        if response.get("id"):
            await state.update_data(task_id=response["id"])
            categories = await get_categories()
            if categories:
                kb = categories_keyboard(categories)
                await message.answer(
                    f"✅ Задача создана: {data['task_title']}\n"
                    f"📅 На {due_datetime.strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"Выберите категорию для задачи:",
                    reply_markup=kb
                )
                await state.set_state(Form.task_category)
            else:
                await message.answer("✅ Задача создана, но категории недоступны.")
                await state.clear()
        else:
            await message.answer(f"Ошибка при создании задачи. {response}")
            await state.clear()

    except ValueError as e:
        logger.warning(f"⚠️ Ошибка парсинга времени: {e}")
        await message.answer("Неверный формат времени. Введите в формате ЧЧ:ММ.")

# 🔹 Обработка выбора категории
@router.callback_query(lambda c: c.data and c.data.startswith("set_category:"))
async def category_chosen_handler(callback: CallbackQuery, state: FSMContext):
    category_id = callback.data.split(":")[1]
    data = await state.get_data()
    task_id = data.get("task_id")
    if not task_id:
        await callback.answer("Не найдена задача для обновления.", show_alert=True)
        return
    success = await update_task(task_id, {"category": category_id})
    if success:
        await callback.answer("Категория выбрана")
        await callback.message.edit_reply_markup()
        await callback.message.answer("Категория задачи обновлена!")
        await state.clear()
    else:
        await callback.answer("Ошибка при обновлении категории", show_alert=True)

# 🔹 Остальные кнопки
@router.callback_query(lambda c: c.data == "get_tasks")
async def handle_get_tasks(callback: CallbackQuery):
    user_id = callback.from_user.id
    tasks = await get_tasks(user_id)
    await callback.message.answer(f"Ваши задачи:\n\n{tasks}")
    await callback.answer()

@router.callback_query(lambda c: c.data == "new_task")
async def handle_new_task(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.task_title)
    await callback.message.answer("Введите заголовок задачи:")
    await callback.answer()
