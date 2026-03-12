import os
import asyncio
import logging
import time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from faster_whisper import WhisperModel

# -------------------------------
# Logging
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# -------------------------------
# Загружаем переменные окружения
# -------------------------------
load_dotenv()  # читает .env

# -------------------------------
# Настройки
# -------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
TMP_DIR = os.getenv("TMP_DIR", "tmp")
os.makedirs(TMP_DIR, exist_ok=True)

# -------------------------------
# Загружаем модель
# -------------------------------
model = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=2)  # tiny/base/small/medium/large

logger.info("Whisper model loaded")

# Очередь задач
queue = asyncio.Queue()

# -------------------------------
# Обработчик очереди
# -------------------------------
async def worker(app):
    logger.info("Worker started")

    while True:
        update, context = await queue.get()
        user = update.message.from_user
        chat_id = update.message.chat_id
        file_id = update.message.voice.file_id

        logger.info(
            f"Start processing voice | user_id={user.id} username={user.username}"
        )

        file = await context.bot.get_file(file_id)
        file_path = os.path.join(TMP_DIR, f"{file_id}.ogg")

        logger.info(f"Downloading file {file_id}")
        
        await file.download_to_drive(file_path)

        logger.info(f"File downloaded: {file_path}")

        # Распознаем
        start_time = time.time()
        logger.info("Start transcription")

        segments, info = model.transcribe(file_path)
        text = " ".join(segment.text for segment in segments).strip()
        duration = time.time() - start_time

        logger.info(
            f"Transcription finished | user_id={user.id} | time={duration:.2f}s"
        )

        # Отправляем результат
        if text:
            logger.info(f"Recognized text: {text[:120]}")

            await context.bot.send_message(chat_id=chat_id, text=text)
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ Не удалось распознать голос.",
                parse_mode="MarkdownV2"
            )

        os.remove(file_path)
        queue.task_done()

# -------------------------------
# Telegram обработчик
# -------------------------------
async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat_id = update.message.chat_id

    logger.info(
        f"Voice received | user_id={user.id} username={user.username} name={user.first_name}"
    )

    # Отправляем промежуточное сообщение
    await context.bot.send_message(
        chat_id=chat_id,
        text="⏳ Обрабатываю ваш голос…",
        parse_mode="MarkdownV2"
    )

    # Добавляем в очередь
    await queue.put((update, context))

# -------------------------------
# Запуск бота
# -------------------------------
if __name__ == "__main__":
    logger.info("Starting Speech2Text bot")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))

    # Запускаем worker
    loop = asyncio.get_event_loop()
    loop.create_task(worker(app))

    logger.info("Bot started and polling Telegram")

    app.run_polling()
