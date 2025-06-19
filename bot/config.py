from pathlib import Path
from dotenv import load_dotenv
import os

# Загрузка .env из корня проекта
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'
load_dotenv(env_path)

#API_URL = os.getenv("DJANGO_API_URL", "http://web:8000/api")
API_URL = os.getenv("DJANGO_API_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
