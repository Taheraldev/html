import os
import subprocess
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters
from bs4 import BeautifulSoup
from googletrans import Translator

# إعداد تسجيل الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# إنشاء مثيل للمترجم
translator = Translator()

# معرف المشرف لاستقبال إشعارات عند دخول مستخدم جديد
ADMIN_ID = os.getenv("ADMIN_ID", "5198110160")

def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    update.message.reply_text("مرحباً! أرسل لي ملف PDF وسأقوم بتحويله إلى HTML مترجم.")
    
    # إرسال إشعار للمشرف عند دخول المستخدم
    admin_message = f"📢 دخل المستخدم:\nمعرف المستخدم: {user.id}\nالاسم: {user.first_name} {user.last_name if user.last_name else ''}\nاسم المستخدم: @{user.username if user.username else 'غير متوفر'}"
    context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)

def convert_pdf_to_html(pdf_path: str, output_dir: str) -> str:
    """
    تحويل PDF إلى HTML باستخدام `pdftohtml` من poppler-utils.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        output_html_path = os.path.join(output_dir, os.path.basename(pdf_path).replace('.pdf', '.html'))
        
        # تشغيل pdftohtml مع تحسين التخطيط وإزالة الإطارات
        subprocess.run(['pdftohtml', '-c', '-noframes', pdf_path, output_html_path],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        return output_html_path
    except subprocess.CalledProcessError as e:
        logger.error("❌ خطأ أثناء تحويل PDF إلى HTML: %s", e.stderr.decode('utf-8'))
        return None

def translate_html(file_path: str) -> str:
    """
    ترجمة محتوى HTML من الإنجليزية إلى العربية.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    
    for element in soup.find_all(text=True):
        original_text = element.strip()
        if original_text:
            try:
                translated_text = translator.translate(original_text, src='en', dest='ar').text
                element.replace_with(translated_text)
            except Exception as e:
                logger.error(f"❌ خطأ أثناء الترجمة: {e}")
    
    translated_html_path = file_path.replace('.html', '_translated.html')
    with open(translated_html_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    return translated_html_path

def handle_pdf(update: Update, context: CallbackContext):
    document = update.message.document
    if document and document.file_name.lower().endswith('.pdf'):
        if document.file_size > 2 * 1024 * 1024:
            update.message.reply_text("❌ حجم الملف أكبر من 2MB. يرجى إرسال ملف PDF أصغر.")
            return
        
        update.message.reply_text("⏳ جاري تحويل ملف PDF إلى HTML وترجمته، انتظر بعض الدقائق...")

        pdf_path = document.file_name
        output_dir = "converted_files"

        new_file = context.bot.get_file(document.file_id)
        new_file.download(pdf_path)
        logger.info("📥 تم تحميل الملف: %s", pdf_path)

        # تحويل PDF إلى HTML
        html_path = convert_pdf_to_html(pdf_path, output_dir)
        if html_path:
            # ترجمة HTML
            translated_html_path = translate_html(html_path)
            with open(translated_html_path, 'rb') as f:
                context.bot.send_document(
                    chat_id=update.message.chat_id,
                    document=f,
                    caption="✅ تم تحويل وترجمة الملف بنجاح!\nقم بإعادة توجيه هذا الملف للبوت الرئيسي لتحويله إلى PDF: @i2pdfbot \n@ta_ja199 للاستفسار"
                )
            update.message.reply_text("✅ تم تحويل الملف إلى HTML مترجم بنجاح!")
        else:
            update.message.reply_text("❌ حدث خطأ أثناء تحويل الملف.")
        
        # تنظيف الملفات المؤقتة
        os.remove(pdf_path)
        os.remove(html_path)
        os.remove(translated_html_path)
    else:
        update.message.reply_text("❌ يرجى إرسال ملف PDF فقط.")

def main():
    token = os.getenv("BOT_TOKEN")

    updater = Updater(token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.document.pdf, handle_pdf))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
