# tasks/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.utils.timezone import now
from .models import Task

@shared_task
def notify_due_tasks():
    due_tasks = Task.objects.filter(due_date__lte=now(), is_done=False)
    for task in due_tasks:
        send_mail(
            subject="Напоминание о задаче",
            message=f"Задача '{task.title}' просрочена!",
            from_email='bot@todolist.com',
            recipient_list=[task.user.email],
        )
