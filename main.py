import os
import subprocess
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
from bs4 import BeautifulSoup
from googletrans import Translator

# إعداد تسجيل الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# إنشاء مثيل للمترجم
translator = Translator()

# جلب متغيرات البيئة
ADMIN_ID = os.getenv("ADMIN_ID", "5198110160")
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: CallbackContext):
    """استجابة عند بدء تشغيل البوت."""
    user = update.message.from_user
    await update.message.reply_text("مرحباً! أرسل لي ملف PDF وسأقوم بتحويله إلى HTML مترجم ثم إلى PDF.")

    # إشعار المشرف عند دخول مستخدم جديد
    admin_message = f"📢 مستخدم جديد:\n🔹 معرف: {user.id}\n🔹 الاسم: {user.first_name} {user.last_name or ''}\n🔹 اسم المستخدم: @{user.username or 'غير متوفر'}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)

def convert_pdf_to_html(pdf_path: str, output_dir: str) -> str:
    """تحويل PDF إلى HTML باستخدام `pdftohtml`."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        output_html_path = os.path.join(output_dir, os.path.basename(pdf_path).replace('.pdf', '.html'))

        subprocess.run(['pdftohtml', '-c', '-noframes', pdf_path, output_html_path], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        return output_html_path
    except subprocess.CalledProcessError as e:
        logger.error("❌ خطأ أثناء تحويل PDF إلى HTML: %s", e.stderr.decode('utf-8'))
        return None

def translate_html(file_path: str) -> str:
    """ترجمة محتوى HTML من الإنجليزية إلى العربية."""
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

def convert_html_to_pdf(html_path: str) -> str:
    """تحويل ملف HTML إلى PDF باستخدام `wkhtmltopdf`."""
    pdf_path = html_path.replace(".html", ".pdf")
    try:
        subprocess.run(['wkhtmltopdf', html_path, pdf_path], check=True)
        return pdf_path
    except subprocess.CalledProcessError as e:
        logger.error("❌ خطأ أثناء تحويل HTML إلى PDF: %s", e.stderr.decode('utf-8'))
        return None

async def handle_pdf(update: Update, context: CallbackContext):
    """معالجة ملفات PDF المرسلة من المستخدم."""
    document = update.message.document
    if document and document.file_name.lower().endswith('.pdf'):
        if document.file_size > 2 * 1024 * 1024:
            await update.message.reply_text("❌ حجم الملف أكبر من 2MB. يرجى إرسال ملف PDF أصغر.")
            return
        
        await update.message.reply_text("⏳ جاري تحويل وترجمة الملف، يرجى الانتظار...")

        pdf_path = document.file_name
        output_dir = "converted_files"

        # تحميل الملف
        new_file = await context.bot.get_file(document.file_id)
        await new_file.download_to_drive(pdf_path)
        logger.info("📥 تم تحميل الملف: %s", pdf_path)

        # تحويل PDF إلى HTML
        html_path = convert_pdf_to_html(pdf_path, output_dir)
        if html_path:
            # ترجمة HTML
            translated_html_path = translate_html(html_path)

            # تحويل HTML إلى PDF
            translated_pdf_path = convert_html_to_pdf(translated_html_path)

            if translated_pdf_path:
                # إرسال الملفات للمستخدم
                with open(translated_html_path, 'rb') as html_file, open(translated_pdf_path, 'rb') as pdf_file:
                    await context.bot.send_document(chat_id=update.message.chat_id, document=html_file, caption="✅ ملف HTML المترجم")
                    await context.bot.send_document(chat_id=update.message.chat_id, document=pdf_file, caption="✅ ملف PDF المترجم")

                await update.message.reply_text("✅ تم تحويل وترجمة الملف بنجاح!")
            else:
                await update.message.reply_text("❌ حدث خطأ أثناء تحويل HTML إلى PDF.")
        else:
            await update.message.reply_text("❌ حدث خطأ أثناء تحويل الملف.")

        # تنظيف الملفات المؤقتة
        os.remove(pdf_path)
        os.remove(html_path)
        os.remove(translated_html_path)
        if translated_pdf_path:
            os.remove(translated_pdf_path)
    else:
        await update.message.reply_text("❌ يرجى إرسال ملف PDF فقط.")

def main():
    """إعداد وتشغيل البوت."""
    app = Application.builder().token(BOT_TOKEN).build()  # تم تصحيحه

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))

    app.run_polling()

if __name__ == '__main__':
    main()
