# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копируем весь проект внутрь контейнера
COPY . /app/

# Команда по умолчанию (можно переопределить)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
