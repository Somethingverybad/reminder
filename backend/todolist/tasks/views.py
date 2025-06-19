from rest_framework import generics, mixins, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Task, Category, TelegramUser
from .serializers import TaskSerializer, CategorySerializer, TelegramUserSerializer


class UserTasksListAPIView(generics.ListAPIView):
    serializer_class = TaskSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get("user")
        category_id = self.request.query_params.get("category_id")

        if not user_id:
            return Task.objects.none()

        queryset = Task.objects.filter(user__telegram_id=user_id, is_done=False)

        if category_id:
            queryset = queryset.filter(category__id=category_id)

        return queryset


class TaskDetailAPIView(mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin,
                        generics.GenericAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    lookup_field = "id"

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class TaskCreateAPIView(generics.CreateAPIView):
    serializer_class = TaskSerializer

class UpdateTaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    lookup_field = "id"
    def get_queryset(self):
        task_id = self.request.query_params.get("user")
        if user_id is not None:
            return Task.objects.filter(user__telegram_id=user_id, is_done=False)
        return Task.objects.none()


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



# Список категорий пользователя
class UserCategoriesListAPIView(generics.ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        telegram_id = self.request.query_params.get("telegram_id")
        if telegram_id:
            return Category.objects.filter(user__telegram_id=telegram_id)
        return Category.objects.none()

# Детальная работа с категорией по id
class CategorieDetailAPIView(mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            generics.GenericAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "id"

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

# Создание категории
class CategoriesCreateAPIView(generics.CreateAPIView):
    serializer_class = CategorySerializer

    def perform_create(self, serializer):
        telegram_id = self.request.data.get("telegram_id")
        if not telegram_id:
            raise PermissionDenied("telegram_id is required to create category")
        try:
            telegram_user = TelegramUser.objects.get(telegram_id=telegram_id)
        except TelegramUser.DoesNotExist:
            raise PermissionDenied("TelegramUser not found")
        serializer.save(user=telegram_user)

