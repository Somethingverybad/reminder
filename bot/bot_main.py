from config import BOT_TOKEN
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers.simple_dialog import router

API_TOKEN = BOT_TOKEN

# В файле, где инициализируется бот (например, bot_main.py)
#print(f"Используемый токен: {BOT_TOKEN}")  # Проверьте вывод
async def main():
    bot = Bot(token=API_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(router)

    try:
        print("Бот запущен")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())