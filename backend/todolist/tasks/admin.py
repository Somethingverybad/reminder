from django.contrib import admin
from .models import Task, Category


admin.site.register(Category)

from tasks.tasks import notify_due_tasks  # импорт задачи Celery

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'is_done','due_date')  # пример полей

    actions = ['send_notifications']

    def send_notifications(self, request, queryset):
        notify_due_tasks.delay()
        self.message_user(request, "Задача notify_due_tasks запущена!")
    send_notifications.short_description = "Запустить отправку уведомлений"