from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import TaskViewSet, CategoryViewSet, TelegramUserRegisterView

router = DefaultRouter()
router.register(r'tasks', TaskViewSet)
router.register(r'categories', CategoryViewSet)

urlpatterns = router.urls + [
    path('register/', TelegramUserRegisterView.as_view(), name='telegram-register'),
]
