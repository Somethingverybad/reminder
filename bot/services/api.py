import aiohttp
from aiogram import types
from config import API_URL

from datetime import datetime

async def get_tasks(user_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/tasks/?user={user_id}") as resp:
            print(await resp.text())  # для отладки
            if resp.status == 200:
                data = await resp.json()
                result = ""
                for t in data:
                    # Преобразование дат в привычный формат
                    created_at = datetime.fromisoformat(t["created_at"]).strftime("%d.%m.%Y %H:%M")
                    due_date = datetime.fromisoformat(t["due_date"]).strftime("%d.%m.%Y %H:%M")

                    # Категории
                    categories = ", ".join([cat.get("name", "") for cat in t.get("categories", [])]) or "Без категории"

                    # Статус
                    status = "✅ Выполнено" if t["is_done"] else "🕓 В процессе"

                    result += (
                        f"📌 <b>{t['title']}</b>\n"
                        f"📝 {t['description']}\n"
                        f"📅 Дата выполнения: {due_date}\n"
                        f"📂 Категории: {categories}\n"
                        f"Создано: {created_at}\n"
                        f"{status}\n"
                    )

                return result or "Нет задач"
            return "Ошибка при загрузке задач"

async def create_task(user_id, title, description, due_date, category_id=None):
    async with aiohttp.ClientSession() as session:
        payload = {
            "title": title,
            "description": description,
            "user": user_id,
            "due_date": due_date,
            "category": category_id,  # 🔥 новая строка
            "is_done": False,
        }
        async with session.post(f"{API_URL}/tasks/", json=payload) as resp:
            text = await resp.text()
            print(f"STATUS: {resp.status}")
            print(f"TEXT: {text}")
            try:
                return await resp.json()
            except Exception:
                return {"error": "Invalid JSON", "status": resp.status, "text": text}
async def get_categories():
    async with aiohttp.ClientSession() as session:

        async with session.get(f"{API_URL}/categories/") as resp:
            print(await resp.text())
            if resp.status == 200:
                return await resp.json()
    return []

async def register_user_api(telegram_user: types.User):
    async with aiohttp.ClientSession() as session:
        payload = {
            "telegram_id": telegram_user.id,
            "username": telegram_user.username,
            "first_name": telegram_user.first_name,
        }
        async with session.post(f"{API_URL}/register/", json=payload) as resp:
            if resp.status == 201 or resp.status == 200:
                return True
            else:
                # можно залогировать ошибку или распарсить сообщение
                return False

async def update_task(task_id: str, payload: dict):
    async with aiohttp.ClientSession() as session:
        async with session.patch(f"{API_URL}/tasks/{task_id}/", json=payload) as resp:
            text = await resp.text()
            print(f"UPDATE STATUS: {resp.status}")
            print(f"UPDATE RESPONSE: {text}")
            if resp.status in (200, 204):
                return True
            return False