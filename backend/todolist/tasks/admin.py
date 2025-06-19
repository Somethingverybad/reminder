from django.contrib import admin
from .models import Task, Category,TelegramUser


admin.site.register(Category)
admin.site.register(TelegramUser)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'is_done','due_date')  # пример полей

    actions = ['send_notifications']