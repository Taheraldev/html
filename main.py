import os
import subprocess
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعداد تسجيل الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("مرحباً! أرسل لي ملف PDF وسأقوم بتحويله إلى HTML.")

def convert_pdf_to_html(pdf_path: str, html_path: str) -> bool:
    """
    يستخدم الأمر pdftohtml لتحويل ملف PDF إلى HTML.
    يُرجى التأكد من تثبيت poppler-utils على النظام.
    """
    try:
        # استخدام الخيارات -c للحفاظ على التخطيط، -noframes لإنتاج HTML بدون إطارات
        result = subprocess.run(
            ['pdftohtml', '-c', '-noframes', pdf_path, html_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"حدث خطأ أثناء تحويل PDF إلى HTML: {e.stderr.decode('utf-8')}")
        return False

def handle_pdf(update: Update, context: CallbackContext):
    document = update.message.document
    if document and document.file_name.lower().endswith('.pdf'):
        # التحقق من حجم الملف (مثلاً لا يتجاوز 2MB)
        if document.file_size > 2 * 1024 * 1024:
            update.message.reply_text("❌ حجم الملف أكبر من 2MB. يرجى إرسال ملف PDF بحجم أصغر.")
            return

        update.message.reply_text("جاري تحويل ملف PDF إلى HTML، انتظر بعض الدقائق...")
        file_id = document.file_id
        original_pdf_path = document.file_name
        html_path = original_pdf_path.replace('.pdf', '.html')

        # تحميل ملف الـ PDF
        new_file = context.bot.get_file(file_id)
        new_file.download(custom_path=original_pdf_path)
        logger.info("تم تحميل الملف: %s", original_pdf_path)

        # تحويل الـ PDF إلى HTML
        if convert_pdf_to_html(original_pdf_path, html_path):
            # إرسال ملف HTML للمستخدم
            with open(html_path, 'rb') as f:
                context.bot.send_document(chat_id=update.message.chat_id, document=f)
            update.message.reply_text("✅ تم تحويل الملف إلى HTML بنجاح!")
        else:
            update.message.reply_text("❌ حدث خطأ أثناء تحويل الملف.")

        # حذف الملفات المؤقتة
        if os.path.exists(original_pdf_path):
            os.remove(original_pdf_path)
        if os.path.exists(html_path):
            os.remove(html_path)
    else:
        update.message.reply_text("يرجى إرسال ملف PDF فقط.")

def main():
    # ضع هنا توكن البوت الخاص بك
    token = "YOUR_BOT_TOKEN"
    
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_pdf))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
