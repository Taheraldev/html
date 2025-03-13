import os
import subprocess
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters

# إعداد تسجيل الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("مرحباً! أرسل لي ملف PDF وسأقوم بتحويله إلى HTML.")

def convert_pdf_to_html(pdf_path: str, html_path: str) -> bool:
    """
    تحويل PDF إلى HTML باستخدام `pdftohtml`.
    يجب تثبيت `poppler-utils` على النظام.
    """
    try:
        subprocess.run(['pdftohtml', '-c', '-noframes', pdf_path, html_path],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("❌ خطأ أثناء تحويل PDF إلى HTML: %s", e.stderr.decode('utf-8'))
        return False

async def handle_pdf(update: Update, context: CallbackContext):
    document = update.message.document
    if document and document.file_name.lower().endswith('.pdf'):
        if document.file_size > 2 * 1024 * 1024:
            await update.message.reply_text("❌ حجم الملف أكبر من 2MB. يرجى إرسال ملف PDF أصغر.")
            return
        
        await update.message.reply_text("⏳ جاري تحويل ملف PDF إلى HTML، انتظر بعض الدقائق...")

        original_pdf_path = document.file_name
        html_path = original_pdf_path.replace('.pdf', '.html')

        new_file = await context.bot.get_file(document.file_id)
        await new_file.download_to_drive(original_pdf_path)
        logger.info("تم تحميل الملف: %s", original_pdf_path)

        if convert_pdf_to_html(original_pdf_path, html_path):
            with open(html_path, 'rb') as f:
                await context.bot.send_document(chat_id=update.message.chat_id, document=f)
            await update.message.reply_text("✅ تم تحويل الملف إلى HTML بنجاح!")
        else:
            await update.message.reply_text("❌ حدث خطأ أثناء تحويل الملف.")
        
        if os.path.exists(original_pdf_path):
            os.remove(original_pdf_path)
        if os.path.exists(html_path):
            os.remove(html_path)
    else:
        await update.message.reply_text("❌ يرجى إرسال ملف PDF فقط.")

def main():
    token = os.getenv("BOT_TOKEN")

    # إنشاء التطبيق باستخدام `Application.builder()`
    app = Application.builder().token(token).build()

    # إضافة المعالجات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))

    # تشغيل البوت
    app.run_polling()

if __name__ == '__main__':
    main()
