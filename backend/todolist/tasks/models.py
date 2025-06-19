
from django.db import models
from django.contrib.auth.models import User
import hashlib
from django.utils.timezone import now

from django.utils.timezone import now

def generate_id(source: str):
    return hashlib.sha256(source.encode()).hexdigest()[:16]


class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username or str(self.telegram_id)

class Category(models.Model):
    id = models.CharField(primary_key=True, max_length=16, editable=False)
    name = models.CharField(max_length=255)
    user = models.ForeignKey(TelegramUser, to_field='telegram_id', on_delete=models.CASCADE, null = True, blank = True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_id(self.name + now().isoformat())
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name





class Task(models.Model):
    id = models.CharField(primary_key=True, max_length=16, editable=False)
    user = models.ForeignKey(TelegramUser, to_field='telegram_id', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    is_done = models.BooleanField(default=False)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)

    # Поля для напоминаний
    remind_daily = models.BooleanField(default=False, verbose_name="Ежедневное напоминание")
    reminder_intervals = models.JSONField(
        default=list,
        blank=True,
        help_text="Список интервалов напоминаний в минутах (например, [60, 1440] для напоминания за 1 час и 1 день)"
    )
    last_reminder_sent = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Время последнего отправленного напоминания"
    )

    def save(self, *args, **kwargs):
        if not self.id:
            source = f"{self.user_id}-{self.title}-{now().isoformat()}"
            self.id = generate_id(source)
        super().save(*args, **kwargs)

    def get_reminder_times(self):
        """Возвращает список datetime объектов, когда нужно отправить напоминания"""
        if not self.due_date:
            return []

        reminder_times = []

        # Добавляем напоминания по интервалам
        for interval in self.reminder_intervals or []:
            reminder_time = self.due_date - timedelta(minutes=interval)
            reminder_times.append(reminder_time)

        # Для ежедневных напоминаний добавляем все дни до даты выполнения
        if self.remind_daily:
            current_day = now().date()
            due_day = self.due_date.date()

            while current_day < due_day:
                reminder_time = datetime.combine(current_day, self.due_date.time())
                if reminder_time > now():  # Не добавляем прошедшие даты
                    reminder_times.append(reminder_time)
                current_day += timedelta(days=1)

        return sorted(reminder_times)

    def get_pending_reminders(self):
        """Возвращает напоминания, которые нужно отправить сейчас"""
        now_time = now()
        pending = []

        for reminder_time in self.get_reminder_times():
            # Проверяем, что напоминание еще не отправлено и время пришло
            if (not self.last_reminder_sent or reminder_time > self.last_reminder_sent) and reminder_time <= now_time:
                pending.append(reminder_time)

        return pending

    def __str__(self):
        return self.title
