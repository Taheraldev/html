import logging
import os
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد نظام تسجيل الأحداث
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# دالة بدء المحادثة
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('مرحباً! أرسل لي ملف PDF وسأقوم بتحويله إلى HTML باستخدام pdftohtml.')

# دالة معالجة الملفات المرسلة
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if document.mime_type != 'application/pdf':
        await update.message.reply_text("الملف المرسل ليس بصيغة PDF.")
        return

    # إنشاء مجلد مؤقت لتحميل الملفات
    os.makedirs("downloads", exist_ok=True)
    
    # تحميل الملف
    input_file = os.path.join("downloads", document.file_name)
    file = await document.get_file()
    await file.download_to_drive(custom_path=input_file)
    
    # تحديد اسم ملف الإخراج (يمكن أن يكون pdftohtml ينتج ملفات متعددة، هنا مثال لتوليد ملف HTML رئيسي)
    output_file = input_file.replace('.pdf', '.html')
    
    try:
        # استخدام pdftohtml لتحويل الملف
        # الخيار -c يحافظ على ألوان النصوص والتخطيط قدر الإمكان
        subprocess.run(['pdftohtml', '-c', input_file, output_file], check=True)
        await update.message.reply_text("تم تحويل الملف بنجاح، جاري إرسال ملف HTML.")
        with open(output_file, 'rb') as html_file:
            await update.message.reply_document(document=html_file)
    except subprocess.CalledProcessError as e:
        logger.error("خطأ أثناء التحويل: %s", e)
        await update.message.reply_text("حدث خطأ أثناء تحويل الملف. تأكد من تثبيت أداة pdftohtml بشكل صحيح.")
    finally:
        # حذف الملفات المؤقتة
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)

def main():
    # ضع توكن بوت تلجرام الخاص بك هنا
    token = '5264968049:AAHUniq68Nqq39CrFf8lVqerwetirQnGxzc'
    application = Application.builder().token(token).build()
    
    # تسجيل المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    
    # بدء البوت
    application.run_polling()

if __name__ == '__main__':
    main()
