import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from googletrans import Translator
from bs4 import BeautifulSoup

# استبدل هذا الرمز برمز API الخاص ببوتك
TOKEN = '6016945663:AAGf2B4dpCo-nVFNXbyPUHuS9XwA1ugGa4Y'

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

        # ترجمة النصوص داخل عناصر HTML
        for element in soup.find_all(text=True):
            if element.parent.name not in ['style', 'script']:  # استثناء عناصر الستايل والسكربت
                translated_text = translator.translate(element, src='ar', dest='en').text
                element.replace_with(translated_text)

        translated_html = str(soup)

        # إرسال الملف المترجم
        context.bot.send_document(chat_id=update.effective_chat.id, document=translated_html.encode('utf-8'), filename='translated.html')

    except Exception as e:
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
