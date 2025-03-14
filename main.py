import os
import subprocess
import logging
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from bs4 import BeautifulSoup
from googletrans import Translator

# إعداد تسجيل الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء مثيل للمترجم
translator = Translator()

# جلب متغيرات البيئة (يمكن تعديلها مباشرة هنا)
ADMIN_ID = os.getenv("ADMIN_ID", "5198110160")
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")  # استبدل YOUR_BOT_TOKEN_HERE بتوكن البوت الخاص بك

def start(update: Update, context: CallbackContext):
    """رسالة الترحيب عند بدء البوت."""
    user = update.message.from_user
    update.message.reply_text("مرحباً! أرسل لي ملف PDF وسأقوم بتحويله إلى HTML مترجم ثم إلى PDF.")
    admin_message = (
        f"📢 مستخدم جديد:\n"
        f"🔹 معرف: {user.id}\n"
        f"🔹 الاسم: {user.first_name} {user.last_name if user.last_name else ''}\n"
        f"🔹 اسم المستخدم: @{user.username if user.username else 'غير متوفر'}"
    )
    context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)

def convert_pdf_to_html(pdf_path: str, output_dir: str) -> str:
    """تحويل ملف PDF إلى HTML باستخدام pdftohtml."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        output_html = os.path.join(output_dir, os.path.basename(pdf_path).replace('.pdf', '.html'))
        subprocess.run(['pdftohtml', '-c', '-noframes', pdf_path, output_html],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return output_html
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode('utf-8') if e.stderr is not None else str(e)
        logger.error("❌ خطأ أثناء تحويل PDF إلى HTML: %s", error_message)
        return None

def translate_html(file_path: str) -> str:
    """ترجمة محتوى HTML من الإنجليزية إلى العربية."""
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    for element in soup.find_all(text=True):
        text = element.strip()
        if text:
            try:
                translation = translator.translate(text, src='en', dest='ar').text
                element.replace_with(translation)
            except Exception as e:
                logger.error("❌ خطأ أثناء الترجمة: %s", e)
    translated_path = file_path.replace('.html', '_translated.html')
    with open(translated_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    return translated_path

def convert_html_to_pdf(html_path: str) -> str:
    """تحويل ملف HTML إلى PDF باستخدام wkhtmltopdf."""
    pdf_path = html_path.replace('.html', '.pdf')
    try:
        subprocess.run(['wkhtmltopdf', html_path, pdf_path], check=True)
        return pdf_path
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode('utf-8') if e.stderr is not None else str(e)
        logger.error("❌ خطأ أثناء تحويل HTML إلى PDF: %s", error_message)
        return None

def handle_pdf(update: Update, context: CallbackContext):
    """معالجة ملف PDF المرسل من المستخدم."""
    document = update.message.document
    if document and document.file_name.lower().endswith('.pdf'):
        if document.file_size > 2 * 1024 * 1024:
            update.message.reply_text("❌ حجم الملف أكبر من 2MB. يرجى إرسال ملف PDF أصغر.")
            return
        update.message.reply_text("⏳ جاري تحويل وترجمة الملف، يرجى الانتظار...")
        
        pdf_path = document.file_name
        output_dir = "converted_files"
        
        # تحميل الملف
        new_file = context.bot.get_file(document.file_id)
        new_file.download(custom_path=pdf_path)
        logger.info("📥 تم تحميل الملف: %s", pdf_path)
        
        # تحويل PDF إلى HTML
        html_path = convert_pdf_to_html(pdf_path, output_dir)
        if not html_path:
            update.message.reply_text("❌ حدث خطأ أثناء تحويل الملف.")
            return
        
        # ترجمة HTML
        translated_html = translate_html(html_path)
        
        # تحويل HTML المترجم إلى PDF
        translated_pdf = convert_html_to_pdf(translated_html)
        
        if translated_pdf:
            with open(translated_html, 'rb') as h_file, open(translated_pdf, 'rb') as p_file:
                context.bot.send_document(
                    chat_id=update.message.chat_id, 
                    document=InputFile(h_file),
                    caption="✅ ملف HTML المترجم"
                )
                context.bot.send_document(
                    chat_id=update.message.chat_id, 
                    document=InputFile(p_file),
                    caption="✅ ملف PDF المترجم"
                )
            update.message.reply_text("✅ تم تحويل وترجمة الملف بنجاح!")
        else:
            update.message.reply_text("❌ حدث خطأ أثناء تحويل HTML إلى PDF.")
        
        # تنظيف الملفات المؤقتة
        for path in [pdf_path, html_path, translated_html, translated_pdf]:
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logger.error("❌ لم يتم حذف الملف %s: %s", path, e)
    else:
        update.message.reply_text("❌ يرجى إرسال ملف PDF فقط.")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document.pdf, handle_pdf))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
