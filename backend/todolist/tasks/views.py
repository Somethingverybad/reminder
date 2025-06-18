from rest_framework import viewsets
from .models import Task, Category, TelegramUser
from .serializers import TaskSerializer, CategorySerializer,TelegramUserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer



class TelegramUserRegisterView(APIView):
    def post(self, request):
        telegram_id = request.data.get('telegram_id')
        if not telegram_id:
            return Response({'error': 'telegram_id is required'}, status=400)

        user, created = TelegramUser.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                'username': request.data.get('username', ''),
                'first_name': request.data.get('first_name', '')
            }
        )

        serializer = TelegramUserSerializer(user)
        return Response(serializer.data, status=201 if created else 200)
