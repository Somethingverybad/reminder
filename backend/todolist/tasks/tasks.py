# tasks/tasks.py

import json
import redis
from celery import shared_task
from django.core.mail import send_mail
from django.utils.timezone import now, timedelta
from django.utils.dateparse import parse_datetime
from .models import Task

# Подключение к Redis (укажи свои настройки при необходимости)
redis_client = redis.Redis(host='redis', port=6379, db=0)


def send_notification(task):
    send_mail(
        subject="Напоминание о задаче",
        message=f"Задача '{task.title}' просрочена!",
        from_email='bot@todolist.com',
        recipient_list=[task.user.email],
    )


@shared_task
def notify_due_tasks():
    # Старая задача, можно оставить или удалить, если перейдёшь на новый механизм
    due_tasks = Task.objects.filter(due_date__lte=now(), is_done=False)
    for task in due_tasks:
        send_notification(task)


@shared_task
def cache_upcoming_tasks():
    interval = timedelta(minutes=10)
    now_time = now()
    upcoming_time = now_time + interval
    tasks = Task.objects.filter(
        due_date__gte=now_time,
        due_date__lte=upcoming_time,
        is_done=False
    ).values('id', 'due_date', 'title', 'user_id')

    # Конвертируем к списку и сериализуем в JSON (из-за datetime - default=str)
    tasks_json = json.dumps(list(tasks), default=str)
    redis_client.set('upcoming_tasks', tasks_json)


@shared_task
def notify_from_cache():
    tasks_json = redis_client.get('upcoming_tasks')
    if not tasks_json:
        return

    tasks = json.loads(tasks_json)
    now_time = now()
    tasks_to_keep = []

    for task in tasks:
        task_due_dt = parse_datetime(task['due_date'])
        if task_due_dt <= now_time:
            # Отправляем уведомление
            try:
                task_obj = Task.objects.get(id=task['id'])
                send_notification(task_obj)
                # Можно пометить задачу как выполненную или уведомленную
                task_obj.is_done = True  # или отдельный флаг, если нужно
                task_obj.save()
            except Task.DoesNotExist:
                # Если задачи уже нет, просто пропускаем
                pass
        else:
            tasks_to_keep.append(task)

    # Обновляем кеш
    redis_client.set('upcoming_tasks', json.dumps(tasks_to_keep, default=str))
