import os
import logging
from dotenv import load_dotenv
from parser import parse_hh_vacancy
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from openai import OpenAI

# Настройка логов
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Инициализация OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text
    await update.message.reply_text("Ссылка получена. Парсю описание…")

    try:
        parsed_result = parse_hh_vacancy(message_text)

        if isinstance(parsed_result, tuple):
            vacancy_text = "\n".join(parsed_result)
        else:
            vacancy_text = parsed_result

        await update.message.reply_text("Описание получено. Генерирую сопроводительное письмо…")

        # Prompt
        system_prompt = (
            'Ты — помощник по написанию сопроводительных писем. Всегда пиши строго по шаблону:\n\n'
            '1. Приветствие: "Здравствуйте! Меня зовут Александр, очень заинтересовала ваша вакансия \\"[название вакансии]\\"."\n'
            '2. Блок с навыками: "Мои ключевые навыки и знания, релевантные вашей вакансии:" — далее список, где каждый пункт начинается с дефиса, заканчивается `;`, последний — точкой.\n'
            '3. Завершение: "На интервью с радостью расскажу о своем опыте подробнее. Спасибо за уделенное время. С уважением, Александр"\n\n'
            'Не добавляй ничего лишнего. Не используй вступления, подписи, “уважаемый работодатель” и прочие клише. Только по шаблону.'
        )

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": vacancy_text}
            ]
        )

        reply_text = response.choices[0].message.content.strip()
        await update.message.reply_text(reply_text)

    except Exception as e:
        logging.error(f"Ошибка при обработке: {e}")
        await update.message.reply_text(f"Ошибка: {e}")

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен 🚀")
    app.run_polling()