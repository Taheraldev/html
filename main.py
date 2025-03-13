import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from googletrans import Translator
from bs4 import BeautifulSoup
import logging

# استبدل هذا الرمز برمز API الخاص ببوتك
TOKEN = '6016945663:AAETwVMU3m27J5lcf7qKlc-90I26ABlY8wA'

# تمكين التسجيل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update, context):
    update.message.reply_text('أرسل لي ملف HTML لترجمته.')

def translate_html(update, context):
    file = context.bot.get_file(update.message.document.file_id)
    file_path = file.download()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')
        translator = Translator()

        for element in soup.find_all(text=True):
            if element and element.strip() and element.parent.name not in ['style', 'script']:
                try:
                    translated_text = translator.translate(element, src='ar', dest='en').text
                    element.replace_with(translated_text)
                except Exception as translate_error:
                    logger.error(f"Translation error: {translate_error}")
                    # يمكنك هنا اضافة بدائل للتعامل مع الخطأ مثل ترك النص بدون ترجمة.

        translated_html = str(soup)

        context.bot.send_document(chat_id=update.effective_chat.id, document=translated_html.encode('utf-8'), filename='translated.html')

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        update.message.reply_text(f'حدث خطأ: {e}')

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document.mime_type('text/html'), translate_html))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
