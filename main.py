import logging
import subprocess
import os
import tempfile
import asyncio
from telegram import Update, filters
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext

# استبدل هذا الرمز برمز API الخاص ببوتك
TOKEN = '6016945663:AAETwVMU3m27J5lcf7qKlc-90I26ABlY8wA'

# تمكين التسجيل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('أرسل لي ملف HTML لترجمته.')

async def translate_html(update: Update, context: CallbackContext):
    file = await context.bot.get_file(update.message.document.file_id)
    file_path = await file.download_to_drive()

    try:
        # إنشاء ملفات مؤقتة
        with tempfile.TemporaryDirectory() as temp_dir:
            po_file = os.path.join(temp_dir, 'output.po')
            translated_po_file = os.path.join(temp_dir, 'translated.po')
            translated_html_file = os.path.join(temp_dir, 'translated.html')

            # استخراج النصوص إلى ملف PO
            subprocess.run(['pofilter', '-i', file_path, '-x', 'html', '-o', po_file], check=True)

            # ترجمة ملف PO باستخدام translate-toolkit
            subprocess.run(['translate', '-i', po_file, '-o', translated_po_file,
                            '--target-language', 'en', '--source-language', 'ar', '--engine', 'google'], check=True)

            # دمج النصوص المترجمة في ملف HTML الأصلي
            subprocess.run(['pomerge', '-i', translated_po_file, '-p', file_path, '-o', translated_html_file], check=True)

            # إرسال الملف المترجم
            with open(translated_html_file, 'rb') as f:
                await context.bot.send_document(chat_id=update.effective_chat.id, document=f, filename='translated.html')

    except subprocess.CalledProcessError as e:
        logger.error(f"Error during translation: {e}")
        await update.message.reply_text('حدث خطأ أثناء الترجمة.')
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        await update.message.reply_text(f'حدث خطأ: {e}')

async def main():
    # إنشاء التطبيق بطريقة حديثة
    app = Application.builder().token(TOKEN).build()

    # إضافة الأوامر والمعالجات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.MimeType('text/html'), translate_html))

    # تشغيل البوت
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
