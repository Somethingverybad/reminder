import logging
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from states import Form
from services.django_api import get_categories, create_category, update_category_api, delete_category_api
from handlers.main_menu import show_main_keyboard

logger = logging.getLogger(__name__)
router = Router()

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

@router.callback_query(lambda c: c.data == "create_cat")
async def create_category_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.category_name)
    await callback.message.answer("Введите название нового тега:")

@router.message(Form.category_name)
async def create_category_name_entered(message: types.Message, state: FSMContext):
    name = message.text.strip()
    user_id = message.from_user.id

    response = await create_category(user_id, name)
    if response.get("id"):
        await message.answer("✅ Тег создан!")
    else:
        await message.answer("❌ Ошибка при создании тега.")
    await state.clear()
    await show_main_keyboard(message)

@router.callback_query(lambda c: c.data.startswith("edit_cat:"))
async def edit_category(callback: CallbackQuery, state: FSMContext):
    cat_id = callback.data.split(":")[1]
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Изменить название", callback_data=f"rename_cat:{cat_id}"),
                InlineKeyboardButton(text="Удалить тег", callback_data=f"delete_cat:{cat_id}")
            ]
        ]
    )
    await callback.message.answer("Выберите действие:", reply_markup=kb)
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("rename_cat:"))
async def rename_category_start(callback: CallbackQuery, state: FSMContext):
    cat_id = callback.data.split(":")[1]
    await state.update_data(editing_cat_id=cat_id)
    await state.set_state(Form.category_rename)
    await callback.message.answer("Введите новое название тега:")
    await callback.answer()

@router.message(Form.category_rename)
async def rename_category_process(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cat_id = data.get("editing_cat_id")
    new_name = message.text.strip()

    success = await update_category_api(cat_id, {"name": new_name})
    if success:
        await message.answer("✅ Название тега успешно изменено!")
    else:
        await message.answer("❌ Ошибка при изменении названия.")

    await state.clear()
    await show_main_keyboard(message)

@router.callback_query(lambda c: c.data.startswith("delete_cat:"))
async def delete_category_confirm(callback: CallbackQuery, state: FSMContext):
    cat_id = callback.data.split(":")[1]
    kb = InlineKeyboardMarkup(
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
    success = await delete_category_api(cat_id)
    if success:
        await callback.message.answer("✅ Тег удалён.")
    else:
        await callback.message.answer("❌ Ошибка при удалении тега.")
    await callback.answer()