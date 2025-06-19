import logging

import aiohttp
from aiogram import types
from config import API_URL

logger = logging.getLogger(__name__)
from datetime import datetime

async def get_tasks(user_id, category=None):
    async with aiohttp.ClientSession() as session:
        if category:
            async with session.get(f"{API_URL}/tasks/user/?user={user_id}&category_id={category}") as resp:
                data = await resp.json()
                print(await resp.text())  # await добавлен
                return data
        else:
            async with session.get(f"{API_URL}/tasks/user/?user={user_id}") as resp:
                data = await resp.json()
                print(await resp.text())  # await добавлен
                return data




async def create_task(
    user_id, 
    title, 
    description, 
    due_date, 
    category_id=None,
    reminder_intervals=None,
    remind_daily=False
):
    async with aiohttp.ClientSession() as session:
        payload = {
            "title": title,
            "description": description,
            "user": user_id,
            "due_date": due_date,
            "category": category_id,
            "is_done": False,
            "reminder_intervals": reminder_intervals or [],
            "remind_daily": remind_daily,
        }
        async with session.post(f"{API_URL}/tasks/", json=payload) as resp:
            text = await resp.text()
            print(f"STATUS: {resp.status}")
            print(f"TEXT: {text}")
            try:
                return await resp.json()
            except Exception:
                return {"error": "Invalid JSON", "status": resp.status, "text": text}

async def create_category(
    user_id,
    name,
):
    async with aiohttp.ClientSession() as session:
        payload = {
            "name": name,
            "telegram_id": user_id,
        }
        async with session.post(f"{API_URL}/categories/", json=payload) as resp:
            text = await resp.text()
            print(f"STATUS: {resp.status}")
            print(f"TEXT: {text}")
            try:
                return await resp.json()
            except Exception:
                return {"error": "Invalid JSON", "status": resp.status, "text": text}

async def get_categories(user_id=None):
    url = f"{API_URL}/categories/user/"

    if user_id:
        url += f"?telegram_id={user_id}"
    print(url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()


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
        print(payload)
        async with session.patch(f"{API_URL}/tasks/{task_id}/", json=payload) as resp:
            text = await resp.text()
            print(f"UPDATE STATUS: {resp.status}")
            print(f"UPDATE RESPONSE: {text}")
            if resp.status in (200, 204):
                return True
            return False


async def update_category_api(cat_id: str, data: dict) -> bool:
    url = f"{API_URL}/categories/{cat_id}/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, json=data) as resp:
                if resp.status == 200:
                    return True
                else:
                    text = await resp.text()
                    logger.error(f"Update category failed: {resp.status} {text}")
                    return False
    except Exception as e:
        logger.error(f"Exception during update_category_api: {e}")
        return False

async def delete_category_api(cat_id: str) -> bool:
    url = f"{API_URL}/categories/{cat_id}/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(url) as resp:
                if resp.status in (200, 204):
                    return True
                else:
                    text = await resp.text()
                    logger.error(f"Delete category failed: {resp.status} {text}")
                    return False
    except Exception as e:
        logger.error(f"Exception during delete_category_api: {e}")
        return False

