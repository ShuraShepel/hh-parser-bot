import os
from parser import parse_hh_vacancy
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]

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

            prompt = (
                "На основе описания вакансии ниже сгенерируй сопроводительное письмо в следующем стиле:\n"
                "- короткое приветствие;\n"
                "- представление: меня зовут Александр. Заинтересовала вакансия \"...\";\n"
                "- блок: 'Мои ключевые навыки и знания, релевантные вашей вакансии:'\n"
                "- список из 7–10 пунктов с ключевыми навыками и опытом;\n"
                "- абзац с фразой: 'На интервью с радостью расскажу о своем опыте подробнее. Спасибо за уделенное время.'\n"
                "- подпись: 'С уважением, Александр'.\n\n"
                f"Описание вакансии:\n{description}"
            )

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=700,
                temperature=0.7
            )

            letter = response.choices[0].message.content.strip()

            # Коррекции
            letter = letter.replace("Здравствуйте!!", "Здравствуйте!")
            letter = letter.replace(
                "Меня зовут Александр, и я заинтересован в позиции Старшего менеджера data-продуктов в вашей компании LaTech.",
                "Меня зовут Александр. Заинтересовала вакансия \"Project Manager (платформа данных)\"."
            )
            letter = letter.replace(
                "Буду рад возможности обсудить мой опыт и как он может быть полезен вашей команде на интервью.",
                "На интервью с радостью расскажу о своем опыте подробнее.\nСпасибо за уделенное время.\nС уважением, Александр"
            )
            letter = letter.replace(
                "С уважением,\nАлександр Шепелев.",
                "На интервью с радостью расскажу о своем опыте подробнее.\nСпасибо за уделенное время.\nС уважением, Александр"
            )
            letter = letter.replace(
                "Я готов обсудить свой опыт и возможный вклад в развитие вашей компании на интервью.",
                "На интервью с радостью расскажу о своем опыте подробнее.\nСпасибо за уделенное время.\nС уважением, Александр"
            )
            letter = letter.replace(
                "Я готов обсудить мой опыт и как я могу принести пользу вашей команде на интервью.",
                "На интервью с радостью расскажу о своем опыте подробнее.\nСпасибо за уделенное время.\nС уважением, Александр"
            )

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