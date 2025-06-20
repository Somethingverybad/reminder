# Reminder Bot

Телеграм-бот для управления напоминаниями, построенный на Django и Docker.

## Требования

- Docker Desktop ([Windows/Mac](https://www.docker.com/products/docker-desktop/)) или Docker Engine (Linux)
- Python 3.11+
- Git

### 1. Клонирование репозитория

```git clone git@github.com:Somethingverybad/reminder.git```

cd reminder

### 2. Настройка окружения
Создайте файл конфигурации по примеру в .env_example:

cp .env_example .env
Отредактируйте .env

# Настройки PostgreSQL
POSTGRES_DB=reminder_db
POSTGRES_USER=reminder_user
POSTGRES_PASSWORD=your_strong_password_here  # Замените на надежный пароль

# Настройки бота
BOT_TOKEN=your_telegram_bot_token  # Получите у @BotFather

# Безопасность Django
SECRET_KEY=your_django_secret_key  # Сгенерируйте ниже

### 3. Генерация SECRET_KEY
Выполните в терминале:

python -c "import secrets; print(secrets.token_urlsafe(50))"
Скопируйте вывод и вставьте в .env после SECRET_KEY=.

### 4. Запуск приложения
Соберите и запустите контейнеры:

docker-compose build
docker-compose up

