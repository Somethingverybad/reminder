from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from states import Form
from services.django_api import create_category_api
from handlers.simple_dialog import router
from handlers.utils import show_main_keyboard

@router.callback_query(lambda c: c.data == "create_cat")
async def create_category_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.category_name)
    await callback.message.answer("Введите название нового тега:")

@router.message(Form.category_name)
async def create_category_name_entered(message: types.Message, state: FSMContext):
    name = message.text.strip()
    user_id = message.from_user.id

    response = await create_category_api(user_id, name)  # реализуй create_category_api на твоей стороне
    if response.get("id"):
        await message.answer("✅ Тег создан!")
    else:
        await message.answer("❌ Ошибка при создании тега.")
    await state.clear()
    await show_main_keyboard(message)

@router.callback_query(lambda c: c.data.startswith("edit_cat:"))
async def edit_category(callback: CallbackQuery, state: FSMContext):
    cat_id = callback.data.split(":")[1]
    # Можно реализовать редактирование: например, изменить название
    await callback.message.answer(f"Вы выбрали тег с id {cat_id}. Редактирование пока не реализовано.")
