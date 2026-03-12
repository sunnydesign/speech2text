import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from faster_whisper import WhisperModel

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

# Загружаем модель один раз
model = WhisperModel("small")  # tiny/base/small/medium/large

# Очередь задач
queue = asyncio.Queue()

# -------------------------------
# Обработчик очереди
# -------------------------------
async def worker(app):
    while True:
        update, context = await queue.get()
        chat_id = update.message.chat_id
        file_id = update.message.voice.file_id
        file = await context.bot.get_file(file_id)
        file_path = os.path.join(TMP_DIR, f"{file_id}.ogg")
        
        await file.download_to_drive(file_path)

        # Распознаем
        segments, info = model.transcribe(file_path)
        text = " ".join(segment.text for segment in segments).strip()

        # Отправляем результат
        if text:
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
    chat_id = update.message.chat_id
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
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))

    # Запускаем worker
    loop = asyncio.get_event_loop()
    loop.create_task(worker(app))

    print("Bot started...")
    app.run_polling()
