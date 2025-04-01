# bot.py

import os
from dotenv import load_dotenv
from parser import parse_hh_vacancy
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from openai import OpenAI
import logging

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Загрузка .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Инициализация OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Обработчик входящих сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text

    try:
        parsed_result = parse_hh_vacancy(message_text)

        # Если результат — кортеж, объединяем его в строку
        if isinstance(parsed_result, tuple):
            vacancy_text = "\n".join(parsed_result)
        else:
            vacancy_text = parsed_result

        # Запрос к OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты помогаешь писать сопроводительные письма. Стиль — краткий, дружелюбный, честный. Без воды."},
                {"role": "user", "content": vacancy_text}
            ]
        )

        reply_text = response.choices[0].message.content
        await update.message.reply_text(f"Сопроводительное письмо:\n\n{reply_text}")

    except Exception as e:
        logging.error(f"Ошибка при обработке сообщения: {e}")
        await update.message.reply_text(f"Ошибка: {e}")

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен 🚀")
    app.run_polling()