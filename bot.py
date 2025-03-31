from parser import parse_hh_vacancy
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import openai
import re

# 🔐 Твои ключи
import os
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
openai.api_key = os.environ["OPENAI_API_KEY"]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id

    if text.startswith("https://hh.ru/vacancy/"):
        await context.bot.send_message(chat_id=chat_id, text="Ссылка получена. Парсю описание…")

        try:
            description, title = parse_hh_vacancy(text)
            if not description:
                await context.bot.send_message(chat_id=chat_id, text="Не удалось найти описание вакансии 😞")
                return

            await context.bot.send_message(chat_id=chat_id, text="Описание получено. Генерирую сопроводительное письмо…")

            prompt = (
                "На основе описания вакансии ниже сгенерируй сопроводительное письмо в следующем стиле:\n"
                "- короткое приветствие;\n"
                "- представление: меня зовут Александр, заинтересовала вакансия;\n"
                "- список из 7–10 ключевых релевантных навыков и опыта (в виде маркеров);\n"
                "- завершающий абзац с фразой про готовность обсудить опыт на интервью;\n"
                "- подпись: С уважением, Александр.\n\n"
                "Описание вакансии:\n"
                f"{description}"
            )

            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=700,
                temperature=0.7
            )

            letter = response.choices[0].message.content.strip()

            # === Коррекция формулировок ===

            # Приветствие — строго "Здравствуйте!"
            letter = re.sub(r"Здравствуйте[!.,]*", "Здравствуйте!", letter)

            # Представление + добавление блока перед навыками
            letter = re.sub(
                r"Меня зовут Александр[^.\n]*[.\n]",
                f'Меня зовут Александр. Заинтересовала вакансия "{title}".\nМои ключевые навыки и знания, релевантные вашей вакансии:',
                letter,
                flags=re.IGNORECASE
            )

            # Удаление лишней фразы "Мои ключевые навыки и опыт включают:"
            letter = re.sub(
                r"\n?Мои ключевые навыки и опыт включают:\n?",
                "",
                letter,
                flags=re.IGNORECASE
            )

            # Удаление любых завершений от GPT и замена на твой финальный блок
            end_variants = [
                r"С удовольствием обсудил бы[^.\n]*\n*",
                r"Я готов обсудить[^.\n]*\n*",
                r"Буду рад обсудить[^.\n]*\n*",
                r"Буду рад возможности обсудить[^.\n]*\n*"
            ]
            for pattern in end_variants:
                letter = re.sub(pattern, "", letter, flags=re.IGNORECASE)

            # Удаление старой подписи (если вдруг осталась)
            letter = re.sub(r"\nС уважением[.,\s]*Александр Шепелев[.]*", "", letter, flags=re.IGNORECASE)
            letter = re.sub(r"\nС уважением[.,\s]*Александр[.]*", "", letter, flags=re.IGNORECASE)

            # Добавляем финальный блок + подпись
            letter = letter.strip() + "\n\nНа интервью с радостью расскажу о своем опыте подробнее.\nСпасибо за уделенное время.\nС уважением, Александр"

            # Telegram ограничение
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