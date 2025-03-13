import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import subprocess
import os
import tempfile

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
        # إنشاء ملفات مؤقتة
        with tempfile.TemporaryDirectory() as temp_dir:
            po_file = os.path.join(temp_dir, 'output.po')
            translated_po_file = os.path.join(temp_dir, 'translated.po')
            translated_html_file = os.path.join(temp_dir, 'translated.html')

            # استخراج النصوص إلى ملف PO
            subprocess.run(['pofilter', '-i', file_path, '-x', 'html', '-o', po_file], check=True)

            # ترجمة ملف PO باستخدام translate-toolkit (يمكنك استخدام خدمة ترجمة أخرى هنا)
            subprocess.run(['translate', '-i', po_file, '-o', translated_po_file, '--target-language', 'en', '--source-language', 'ar', '--engine', 'google'], check=True)

            # دمج النصوص المترجمة في ملف HTML الأصلي
            subprocess.run(['pomerge', '-i', translated_po_file, '-p', file_path, '-o', translated_html_file], check=True)

            # إرسال الملف المترجم
            with open(translated_html_file, 'rb') as f:
                context.bot.send_document(chat_id=update.effective_chat.id, document=f, filename='translated.html')

    except subprocess.CalledProcessError as e:
        logger.error(f"Error during translation: {e}")
        update.message.reply_text('حدث خطأ أثناء الترجمة.')
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        update.message.reply_text(f'حدث خطأ: {e}')

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document.mime_type('text/html'), translate_html))

    while True:
        try:
            updater.start_polling()
            updater.idle()
        except telegram.error.TimedOut:
            logging.warning("Connection timed out. Retrying in 10 seconds...")
            time.sleep(10)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            time.sleep(10)

if __name__ == '__main__':
    main()
