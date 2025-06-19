FROM python:3.11-slim

# Установка tzdata и настройка часового пояса
RUN apt-get update && \
    apt-get install -y tzdata && \
    ln -sf /usr/share/zoneinfo/America/Adak /etc/localtime && \
    echo "America/Adak" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /bot
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "bot_main.py"]
