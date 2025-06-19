from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from handlers.main_menu import show_main_keyboard

router = Router()

@router.message(lambda message: message.text == "❌ Отмена")
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    await show_main_keyboard(message)