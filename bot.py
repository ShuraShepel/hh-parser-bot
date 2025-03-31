from dotenv import load_dotenv
from pathlib import Path
import os
from openai import OpenAI
from parser import parse_hh_vacancy
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# === Загрузка .env ===
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id

    if text.startswith("https://hh.ru/vacancy/"):
        await context.bot.send_message(chat_id=chat_id, text="Ссылка получена. Парсю описание…")

        try:
            description = parse_hh_vacancy(text)
            if not description or "Не удалось найти" in description:
                await context.bot.send_message(chat_id=chat_id, text="Не удалось найти описание вакансии 😞")
                return

            await context.bot.send_message(chat_id=chat_id, text="Описание получено. Генерирую сопроводительное письмо…")

            # Получение названия вакансии
            title_line = next((line for line in description.splitlines() if line.strip()), "")
            vacancy_title = title_line.strip()[:80]

            prompt = (
                "На основе описания вакансии ниже сгенерируй сопроводительное письмо в следующем стиле:\n"
                "- короткое приветствие;\n"
                "- представление: меня зовут Александр. Заинтересовала вакансия \"{vacancy_title}\".\n"
                "- строка: Мои ключевые навыки и знания, релевантные вашей вакансии:\n"
                "- список из 7–10 пунктов с опытом и навыками;\n"
                "- финальный абзац: На интервью с радостью расскажу о своем опыте подробнее. Спасибо за уделенное время.\n"
                "- подпись: С уважением, Александр.\n\n"
                f"Описание вакансии:\n{description}"
            )

            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7
            )

            letter = completion.choices[0].message.content.strip()

            # Жёсткая финальная замена концовки
            letter = letter.rsplit("С уважением", 1)[0].strip()
            letter += "\n\nНа интервью с радостью расскажу о своем опыте подробнее.\nСпасибо за уделенное время.\nС уважением, Александр"

            if len(letter) > 4000:
                letter = letter[:3990] + "\n\n(обрезано)"

            await context.bot.send_message(chat_id=chat_id, text=letter)

        except Exception as e:
            await context.bot.send_message(chat_id=chat_id, text=f"Ошибка: {e}")
    else:
        await context.bot.send_message(chat_id=chat_id, text="Пришли ссылку на вакансию с hh.ru")


if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    print("Бот запущен 🚀")
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()