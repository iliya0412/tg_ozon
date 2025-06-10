import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials

LOGIN, WEEK = range(2)

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = ServiceAccountCredentials.from_json_keyfile_name("proizvod-49f7ea2db080.json", SCOPE)
client = gspread.authorize(CREDS)
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1TI1VGYBDvsRinBVHAPf1wZDvBN-rRCW_Fic6Q9-5nqA/edit?usp=sharing"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Привет коллега! Я могу показать твои результаты за неделю.\n"
        "Для начала дай мне свой логин. Пиши нижним регистром — так мне будет проще."
    )
    return LOGIN

def get_login(update: Update, context: CallbackContext) -> int:
    login = update.message.text.strip().lower()
    context.user_data['login'] = login
    update.message.reply_text(f"Отлично, {login}. Теперь скажи мне результаты какой недели тебя интересуют, в формате W1.")
    return WEEK

def get_week(update: Update, context: CallbackContext) -> int:
    week = update.message.text.strip().upper()
    login = context.user_data.get('login')

    try:
        sheet = client.open_by_url(SPREADSHEET_URL)
    except Exception as e:
        update.message.reply_text("Ошибка подключения к таблице.")
        logging.error(e)
        return ConversationHandler.END

    found = False
    result_message = ""

    for worksheet in sheet.worksheets():
        try:
            records = worksheet.get_all_records()
            for row in records:
                if row.get('login', '').lower() == login and row.get('week', '').upper() == week:
                    found = True
                    result_message += f"\n📄 Лист: *{worksheet.title}*\n"
                    for key, value in row.items():
                        if key.lower() not in ['week', 'login']:
                            result_message += f"• {key}: {value}\n"
        except Exception as e:
            logging.warning(f"Ошибка при обработке листа {worksheet.title}: {e}")

    if found:
        update.message.reply_text(result_message.strip(), parse_mode="Markdown")
    else:
        update.message.reply_text("Не удалось найти данные по указанному логину и неделе.")

    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Окей, отмена.")
    return ConversationHandler.END

def main():
    updater = Updater("7573170013:AAHV1uLLPGh1Uzt1Udu510Y3Bqtvk0c8vjM", use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LOGIN: [MessageHandler(Filters.text & ~Filters.command, get_login)],
            WEEK: [MessageHandler(Filters.text & ~Filters.command, get_week)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
