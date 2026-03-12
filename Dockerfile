# -------------------------------
# Dockerfile для speech2text
# -------------------------------

# Базовый образ с Python 3.10
FROM python:3.10-slim

# Устанавливаем зависимости для сборки ffmpeg (нужен для faster-whisper)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем файлы проекта
COPY . /app

# Создаем папку tmp внутри контейнера
RUN mkdir -p /app/tmp && chmod 777 /app/tmp

# Устанавливаем Python-зависимости
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Команда по умолчанию при старте контейнера
CMD ["python", "speech2text.py"]