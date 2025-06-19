
import logging
from datetime import datetime, timedelta, date

from aiogram import Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from services.django_api import *
from states import Form
from handlers.utils import *
from aiogram.utils.text_decorations import html_decoration as html


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
            [KeyboardButton(text="🏷 Теги")],  # новая кнопка для тегов
            [KeyboardButton(text="❌ Отмена")]
        ], resize_keyboard=True
    )
    await message.answer("Главное меню:", reply_markup=kb)


@router.message(lambda message: message.text == "🏷 Теги")
async def show_user_categories(message: types.Message):
    categories = await get_categories(user_id=message.from_user.id)
    if not categories:
        await message.answer("У вас пока нет тегов.")
        return

    buttons = [
        [InlineKeyboardButton(text=cat["name"], callback_data=f"edit_cat:{cat['id']}")]
        for cat in categories
    ]
    buttons.append([InlineKeyboardButton(text="➕ Создать новый тег", callback_data="create_cat")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer("Ваши теги:", reply_markup=kb)




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
    """Создаёт задачу сразу после выбора времени, без напоминаний"""
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

            categories = await get_categories(user_id=user_id)
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



@router.callback_query(lambda c: c.data.startswith("done:"))
async def mark_task_done(callback: CallbackQuery):
    task_id = callback.data.split(":")[1]

    success = await update_task(task_id, {"is_done": True})

    if success:
        await callback.message.edit_text("✅ Задача отмечена как выполненная.")
    else:
        await callback.message.answer("❌ Не удалось обновить задачу.")

    await callback.answer()

@router.callback_query(lambda c: c.data == "create_cat")
async def create_category_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.category_name)
    await callback.message.answer("Введите название нового тега:")

@router.message(Form.category_name)
async def create_category_name_entered(message: types.Message, state: FSMContext):
    name = message.text.strip()
    user_id = message.from_user.id

    response = await create_category (user_id, name)  # реализуй create_category_api на твоей стороне
    if response.get("id"):
        await message.answer("✅ Тег создан!")
    else:
        await message.answer("❌ Ошибка при создании тега.")
    await state.clear()
    await show_main_keyboard(message)


@router.callback_query(lambda c: c.data.startswith("edit_cat:"))
async def edit_category(callback: CallbackQuery, state: FSMContext):
    cat_id = callback.data.split(":")[1]

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Изменить название", callback_data=f"rename_cat:{cat_id}"),
                InlineKeyboardButton(text="Удалить тег", callback_data=f"delete_cat:{cat_id}")
            ]
        ],
        row_width=2
    )
    await callback.message.answer("Выберите действие:", reply_markup=kb)


@router.callback_query(lambda c: c.data.startswith("rename_cat:"))
async def rename_category_start(callback: CallbackQuery, state: FSMContext):
    cat_id = callback.data.split(":")[1]
    await state.update_data(editing_cat_id=cat_id)
    await state.set_state(Form.category_rename)  # Добавьте это состояние в Form
    await callback.message.answer("Введите новое название тега:")
    await callback.answer()


@router.message(Form.category_rename)
async def rename_category_process(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cat_id = data.get("editing_cat_id")
    new_name = message.text.strip()

    # Логика обновления категории через API
    success = await update_category_api(cat_id, {"name": new_name})  # Реализуйте update_category_api

    if success:
        await message.answer("✅ Название тега успешно изменено!")
    else:
        await message.answer("❌ Ошибка при изменении названия.")

    await state.clear()
    await show_main_keyboard(message)


@router.callback_query(lambda c: c.data.startswith("delete_cat:"))
async def delete_category_confirm(callback: CallbackQuery, state: FSMContext):
    cat_id = callback.data.split(":")[1]
    kb = InlineKeyboardMarkup(row_width=2,
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, удалить", callback_data=f"confirm_delete_cat:{cat_id}"),
                InlineKeyboardButton(text="Отмена", callback_data="cancel_delete_cat")
            ]
        ]
    )
    await callback.message.answer("Вы уверены, что хотите удалить тег?", reply_markup=kb)
    await callback.answer()


@router.callback_query(lambda c: c.data == "cancel_delete_cat")
async def cancel_delete_category(callback: CallbackQuery):
    await callback.message.answer("Удаление тега отменено.")
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("confirm_delete_cat:"))
async def delete_category(callback: CallbackQuery):
    cat_id = callback.data.split(":")[1]

    success = await delete_category_api(cat_id)  # Реализуйте delete_category_api

    if success:
        await callback.message.answer("✅ Тег удалён.")
    else:
        await callback.message.answer("❌ Ошибка при удалении тега.")

    await callback.answer()


@router.callback_query(Form.task_category, lambda c: c.data.startswith("set_category:"))
async def process_task_category(callback: CallbackQuery, state: FSMContext):
    category_id = callback.data.split(":")[1]
    data = await state.get_data()
    print(category_id)
    if await update_task(data["task_id"], {"category_id": category_id}):
        await callback.message.answer("✅ Категория сохранена")
    else:
        await callback.message.answer("❌ Ошибка сохранения категории")

    await callback.answer()
    await state.clear()
    await show_main_keyboard(callback.message)

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

    # Повторно показываем выбор категорий
    categories = await get_categories(user_id=callback.from_user.id)

    buttons = [[InlineKeyboardButton(text="📋 Все задачи", callback_data="filter_cat:all")]]
    for cat in categories:
        buttons.append([InlineKeyboardButton(text=cat["name"], callback_data=f"filter_cat:{cat['id']}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.answer("Выберите категорию задач:", reply_markup=kb)
    await callback.answer()


@router.message(lambda message: message.text == "❌ Отмена")
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    await show_main_keyboard(message)
