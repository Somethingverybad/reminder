from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import *

router = DefaultRouter()


urlpatterns = router.urls + [
    path('tasks/user/', UserTasksListAPIView.as_view(), name='user-tasks-list'),  # список задач пользователя
    path('tasks/<str:id>/', TaskDetailAPIView.as_view(), name='task-detail'),   # детальная работа с задачей по id
    path('register/', TelegramUserRegisterView.as_view(), name='telegram-register'),
    path('tasks/', TaskCreateAPIView.as_view(), name='task-create'),

    path('categories/user/', UserCategoriesListAPIView.as_view(), name='user-cat-list'),
    path('categories/<str:id>/', CategorieDetailAPIView.as_view(), name='cat-detail'),
    path('categories/', CategoriesCreateAPIView.as_view(), name='cat-create'),
]
