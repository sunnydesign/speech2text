# -------------------------------
# Dockerfile для speech2text
# -------------------------------

# Базовый образ с Python 3.10
FROM python:3.10-slim

# уменьшаем расход памяти pip
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1

# Устанавливаем зависимости для сборки ffmpeg (нужен для faster-whisper)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# копируем только requirements сначала (лучше кэшируется)
COPY requirements.txt .

# обновляем pip
RUN pip install --upgrade pip setuptools wheel

# ставим самые тяжелые пакеты отдельно
RUN pip install numpy
RUN pip install onnxruntime
RUN pip install ctranslate2
RUN pip install faster-whisper

# ставим остальные зависимости
RUN pip install -r requirements.txt

# копируем код после установки зависимостей
COPY . .

# Создаем папку tmp внутри контейнера
RUN mkdir -p /app/tmp && chmod 777 /app/tmp

# Команда по умолчанию при старте контейнера
CMD ["python", "speech2text.py"]