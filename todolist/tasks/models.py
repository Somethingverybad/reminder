
from django.db import models
from django.contrib.auth.models import User
import hashlib
from django.utils.timezone import now


def generate_id(source: str):
    return hashlib.sha256(source.encode()).hexdigest()[:16]


class Category(models.Model):
    id = models.CharField(primary_key=True, max_length=16, editable=False)
    name = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_id(self.name + now().isoformat())
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Task(models.Model):
    id = models.CharField(primary_key=True, max_length=16, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    is_done = models.BooleanField(default=False)
    categories = models.ManyToManyField(Category, blank=True)

    def save(self, *args, **kwargs):
        if not self.id:
            source = f"{self.user_id}-{self.title}-{now().isoformat()}"
            self.id = generate_id(source)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
