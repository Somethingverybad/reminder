import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

import requests
import redis
from celery import shared_task
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.timezone import now
from .models import Task

# Инициализация логгера
logger = logging.getLogger(__name__)

# Подключение к Redis
try:
    redis_client = redis.Redis(
        host='redis',
        port=6379,
        db=0,
        socket_timeout=5,
        socket_connect_timeout=5
    )
    redis_client.ping()  # Проверка соединения
except redis.ConnectionError as e:
    logger.error(f"Redis connection error: {e}")
    raise

@shared_task(bind=True, name='tasks.tasks.send_telegram_notification')
def send_telegram_notification(self, chat_id: int, message: str):
    """Отправка уведомления через Telegram Bot API с обработкой ошибок"""
    try:
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram notification failed: {e}")
        self.retry(exc=e, countdown=60, max_retries=3)
        return False

@shared_task(bind=True, name='tasks.tasks.send_due_task_reminders')
def send_due_task_reminders(self):
    """Проверка задач, срок выполнения которых наступил, и отправка уведомлений"""
    try:
        now_time = now()
        due_tasks = Task.objects.filter(
            due_date__lte=now_time,
            is_done=False,
        ).filter(
            models.Q(last_reminder_sent__isnull=True) |
            models.Q(last_reminder_sent__lt=models.F('due_date'))
        ).select_related('user')

        logger.info(f"Due tasks found: {due_tasks.count()}")

        for task in due_tasks:
            try:
                message = (
                    f"🔔 Напоминание: {task.title}\n"
                    f"📃 Описание: {task.description}\n"
                    f"📅 Время: {task.due_date.strftime('%Y-%m-%d %H:%M')}"
                )

                send_telegram_notification.delay(task.user.telegram_id, message)

                task.last_reminder_sent = now_time
                task.is_done=True
                task.save(update_fields=["last_reminder_sent", "is_done"])

            except Exception as e:
                logger.error(f"Failed to send reminder for task {task.id}: {e}")

        return True

    except Exception as e:
        logger.error(f"check_due_tasks failed: {e}")
        self.retry(exc=e, countdown=60, max_retries=3)
        return False

@shared_task(bind=True, name='tasks.tasks.delete_completed_tasks')
def delete_completed_tasks(self):
    """Удаление выполненных просроченных задач"""
    try:
        now_time = now()
        completed_tasks = Task.objects.filter(
            due_date__lte=now_time,
            is_done=True,
            remind_daily = False
        )

        logger.info(f"Tasks to delete: {completed_tasks.count()}")

        for task in completed_tasks:
            try:
                logger.info(f"Удаляем задачу {task.id} - {task.title}")
                task.delete()
            except Exception as e:
                logger.error(f"Failed to delete task {task.id}: {e}")

        return True

    except Exception as e:
        logger.error(f"delete_completed_tasks failed: {e}")
        self.retry(exc=e, countdown=60, max_retries=3)
        return False
