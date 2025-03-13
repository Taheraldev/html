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

def convert_pdf_to_html(pdf_path: str, output_dir: str) -> str:
    """
    تحويل PDF إلى HTML باستخدام `pdftohtml` من poppler-utils.
    يتم حفظ المخرجات في مجلد معين لتجنب الفوضى.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)  # إنشاء مجلد الإخراج إذا لم يكن موجودًا
        output_html_path = os.path.join(output_dir, os.path.basename(pdf_path).replace('.pdf', '.html'))
        
        # تشغيل pdftohtml مع تحسين التخطيط وإزالة الإطارات
        subprocess.run(['pdftohtml', '-c', '-noframes', pdf_path, output_html_path],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        return output_html_path
    except subprocess.CalledProcessError as e:
        logger.error("❌ خطأ أثناء تحويل PDF إلى HTML: %s", e.stderr.decode('utf-8'))
        return None

async def handle_pdf(update: Update, context: CallbackContext):
    document = update.message.document
    if document and document.file_name.lower().endswith('.pdf'):
        if document.file_size > 2 * 1024 * 1024:
            await update.message.reply_text("❌ حجم الملف أكبر من 2MB. يرجى إرسال ملف PDF أصغر.")
            return
        
        await update.message.reply_text("⏳ جاري تحويل ملف PDF إلى HTML، انتظر بعض الدقائق...")

        pdf_path = document.file_name
        output_dir = "converted_files"

        new_file = await context.bot.get_file(document.file_id)
        await new_file.download_to_drive(pdf_path)
        logger.info("📥 تم تحميل الملف: %s", pdf_path)

        # تحويل PDF إلى HTML
        html_path = convert_pdf_to_html(pdf_path, output_dir)
        if html_path:
            with open(html_path, 'rb') as f:
                await context.bot.send_document(chat_id=update.message.chat_id, document=f)
            await update.message.reply_text("✅ تم تحويل الملف إلى HTML بنجاح!")
        else:
            await update.message.reply_text("❌ حدث خطأ أثناء تحويل الملف.")
        
        # تنظيف الملفات المؤقتة
        os.remove(pdf_path)
        if html_path and os.path.exists(html_path):
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
