import os
from celery import Celery
from celery.schedules import crontab

# Установка переменной окружения для Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'todolist.settings')

app = Celery('todolist')

# Конфигурация из настроек Django с префиксом 'CELERY_'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическое обнаружение задач в файлах tasks.py приложений
app.autodiscover_tasks()

# Настройка расписания периодических задач

app.conf.beat_schedule = {
    'send-due-task-reminders-every-minute': {
        'task': 'tasks.tasks.send_due_task_reminders',
        'schedule': crontab(minute='*'),
    },
    'delete-completed-tasks-every-10-minutes': {
        'task': 'tasks.tasks.delete_completed_tasks',
        'schedule': crontab(minute='*/10'),
    },
}

# Опционально: глобальные настройки Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Adak',
    enable_utc=True,
)