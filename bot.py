
import logging
import os
import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

TOKEN = "8128628004:AAEGqc1kIvZV-z3jh3VPkvTyWVlEEd01wLA"
LOGIN, WEEK = range(2)

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
GOOGLE_CREDENTIALS = json.loads(os.environ.get("GOOGLE_CREDENTIALS", "{}"))
CREDS = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDENTIALS, SCOPE)
client = gspread.authorize(CREDS)

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1TI1VGYBDvsRinBVHAPf1wZDvBN-rRCW_Fic6Q9-5nqA/edit?usp=sharing"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Привет коллега! Я могу показать твои результаты за неделю.\n"
        "Для начала дай мне свой логин. Пиши нижним регистром — так мне будет проще."
    )
    return LOGIN

async def get_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    login = update.message.text.strip().lower()
    context.user_data["login"] = login
    await update.message.reply_text(
        f"Отлично, {login}. Теперь скажи мне результаты какой недели тебя интересуют, в формате W1."
    )
    return WEEK

async def get_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    week = update.message.text.strip().upper()
    login = context.user_data.get("login")
    try:
        sheet = client.open_by_url(SPREADSHEET_URL)
    except Exception as e:
        await update.message.reply_text("Ошибка подключения к таблице.")
        logging.error(e)
        return ConversationHandler.END

    found = False
    result_message = ""
    for worksheet in sheet.worksheets():
        try:
            records = worksheet.get_all_records()
            for row in records:
                if row.get("login", "").lower() == login and row.get("week", "").upper() == week:
                    found = True
                    result_message += f"\n📄 Лист: *{worksheet.title}*\n"
                    for key, value in row.items():
                        if key.lower() not in ["week", "login"]:
                            result_message += f"• {key}: {value}\n"
        except Exception as e:
            logging.warning(f"Ошибка при обработке листа {worksheet.title}: {e}")

    if found:
        await update.message.reply_text(result_message.strip(), parse_mode="Markdown")
    else:
        await update.message.reply_text("Не удалось найти данные по указанному логину и неделе.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Окей, отмена.")
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_login)],
            WEEK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_week)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
