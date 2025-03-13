import os
import logging
import subprocess
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from bs4 import BeautifulSoup
from googletrans import Translator

# إعداد تسجيل الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء مثيل للمترجم
translator = Translator()

# معرف المشرف
ADMIN_ID = os.getenv("ADMIN_ID", "5198110160")  # استبدل بـ ID المشرف الحقيقي

def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    update.message.reply_text("مرحباً، أرسل لي ملف PDF لتحويله إلى HTML أو أرسل ملف HTML لأقوم بترجمته من الإنجليزية إلى العربية.")
    admin_message = f"دخل المستخدم:\nمعرف المستخدم: {user.id}\nالاسم: {user.first_name} {user.last_name if user.last_name else ''}\nاسم المستخدم: @{user.username if user.username else 'غير متوفر'}"
    context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)

def translate_html(file_path: str) -> str:
    """ يقرأ ملف HTML ويترجم النصوص من الإنجليزية إلى العربية """
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
                logger.error(f"حدث خطأ أثناء الترجمة: {e}")
    return str(soup)

def convert_pdf_to_html(pdf_path: str, output_html_path: str):
    """ يحول ملف PDF إلى HTML باستخدام poppler-utils (pdf2htmlEX) """
    try:
        subprocess.run(["pdf2htmlEX", pdf_path, output_html_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"فشل تحويل PDF إلى HTML: {e}")
        return False

def handle_file(update: Update, context: CallbackContext):
    document = update.message.document
    if document:
        file_name = document.file_name
        file_extension = file_name.split('.')[-1].lower()

        if file_extension not in ['html', 'pdf']:
            update.message.reply_text("❌ يرجى إرسال ملف بصيغة PDF أو HTML فقط.")
            return

        if document.file_size > 2 * 1024 * 1024:
            update.message.reply_text("❌ حجم الملف أكبر من 2MB. يرجى إرسال ملف بحجم أصغر.")
            return

        file_id = document.file_id
        new_file = context.bot.get_file(file_id)
        original_file_path = f"downloaded_{file_name}"
        new_file.download(custom_path=original_file_path)
        logger.info("تم تحميل الملف إلى %s", original_file_path)

        if file_extension == 'html':
            update.message.reply_text("جاري ترجمة ملف HTML، يرجى الانتظار...")
            translated_html = translate_html(original_file_path)
            translated_file_path = f"translated_{file_name}"
            with open(translated_file_path, 'w', encoding='utf-8') as f:
                f.write(translated_html)

            context.bot.send_document(
                chat_id=update.message.chat_id,
                document=open(translated_file_path, 'rb'),
                caption="✅ تم الترجمة بنجاح!"
            )

            os.remove(original_file_path)
            os.remove(translated_file_path)

        elif file_extension == 'pdf':
            update.message.reply_text("🔄 جاري تحويل PDF إلى HTML، يرجى الانتظار...")
            output_html_path = f"converted_{file_name.replace('.pdf', '.html')}"
            success = convert_pdf_to_html(original_file_path, output_html_path)

            if success:
                context.bot.send_document(
                    chat_id=update.message.chat_id,
                    document=open(output_html_path, 'rb'),
                    caption="✅ تم تحويل PDF إلى HTML بنجاح!"
                )
                os.remove(output_html_path)
            else:
                update.message.reply_text("❌ حدث خطأ أثناء تحويل PDF إلى HTML.")

            os.remove(original_file_path)

def main():
    token = "5264968049:AAHUniq68Nqq39CrFf8lVqerwetirQnGxzc"  # ضع توكن البوت هنا

    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_file))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
