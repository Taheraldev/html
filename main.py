import os
import subprocess
import logging
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from bs4 import BeautifulSoup
from googletrans import Translator
from datetime import datetime
import json
import time
from PyPDF2 import PdfFileReader

# إعداد تسجيل الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء مثيل للمترجم
translator = Translator()

# جلب متغيرات البيئة (تأكد من تعديل BOT_TOKEN إلى توكن البوت الخاص بك)
ADMIN_ID = os.getenv("ADMIN_ID", "5198110160")
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
USER_FILE = "user_data.json"

# تحميل بيانات المستخدمين من ملف أو إنشاء ملف جديد إذا لم يكن موجود
def load_user_data():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(USER_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# جلب البيانات الخاصة بالمستخدمين
user_data = load_user_data()

def start(update: Update, context: CallbackContext):
    """رسالة الترحيب عند بدء البوت."""
    user = update.message.from_user
    user_id = str(user.id)
    
    # إرسال رسالة في المرة الأولى فقط
    if user_id not in user_data:
        user_data[user_id] = {
            "used_today": 0,
            "last_used": str(datetime.now().date())
        }
        save_user_data(user_data)
        
        admin_message = (
            f"📢 مستخدم جديد:\n"
            f"🔹 معرف: {user.id}\n"
            f"🔹 الاسم: {user.first_name} {user.last_name if user.last_name else ''}\n"
            f"🔹 اسم المستخدم: @{user.username if user.username else 'غير متوفر'}"
        )
        context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)
        
    # إضافة زر في رسالة الترحيب
    welcome_message = (
        "مرحبا انا بوت اقوم بترجمة ملفات pdf \n"
        "البوت تابع ل: @i2pdfbot \n"
        "ملاحضة البوت تجريبي فقط وسوف يتم تطويره قريبا \n"
        "@ta_ja199 لاستفسار"
    )
    
    keyboard = [
        [InlineKeyboardButton("قناة البوت", url="https://t.me/i2pdfbotchannel")]
    ]
    
    update.message.reply_text(welcome_message, reply_markup=InlineKeyboardMarkup(keyboard))

def send_progress(update: Update, context: CallbackContext, message_id: int, progress: int):
    """إرسال تحديث للمستخدم حول نسبة التقدم في التحويل."""
    progress_bar = "◾️" * (progress // 10) + "◽️" * (10 - progress // 10)
    context.bot.edit_message_text(
        text=f"⏳ جاري تحويل وترجمة الملف، يرجى الانتظار...\n{progress_bar} {progress}%",
        chat_id=update.message.chat_id,
        message_id=message_id,
        parse_mode=ParseMode.MARKDOWN
    )

def get_pdf_page_count(pdf_path: str) -> int:
    """إرجاع عدد الصفحات في ملف PDF."""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PdfFileReader(f)
            return reader.getNumPages()
    except Exception as e:
        logger.error("❌ خطأ أثناء قراءة عدد الصفحات: %s", e)
        return 0

def convert_pdf_to_html(pdf_path: str, output_dir: str, update: Update, context: CallbackContext, message_id: int) -> str:
    """تحويل ملف PDF إلى HTML باستخدام pdftohtml."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        output_html = os.path.join(output_dir, os.path.basename(pdf_path).replace('.pdf', '.html'))
        
        total_pages = get_pdf_page_count(pdf_path)
        if total_pages > 5:
            update.message.reply_text("❌ الحد الأقصى لعدد الصفحات هو 5 صفحات. يرجى إرسال ملف PDF يحتوي على 5 صفحات أو أقل.")
            return None
        
        subprocess.run(['pdftohtml', '-c', '-noframes', pdf_path, output_html],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        # إرسال تحديث نسبة التحميل أثناء التحويل
        for progress in range(0, 101, 10):
            send_progress(update, context, message_id, progress)
            time.sleep(1)  # لتجربة التقدم الفعلي
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
    """تحويل ملف HTML إلى PDF باستخدام wkhtmltopdf مع تمكين الوصول للملفات المحلية."""
    pdf_path = html_path.replace('.html', '.pdf')
    try:
        subprocess.run(['wkhtmltopdf', '--enable-local-file-access', html_path, pdf_path], check=True)
        return pdf_path
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode('utf-8') if e.stderr is not None else str(e)
        logger.error("❌ خطأ أثناء تحويل HTML إلى PDF: %s", error_message)
        return None

def handle_pdf(update: Update, context: CallbackContext):
    """معالجة ملف PDF المرسل من المستخدم."""
    user = update.message.from_user
    user_id = str(user.id)
    today_date = str(datetime.now().date())
    
    # تحقق من عدد الملفات المرسلة في اليوم
    if user_data[user_id]["last_used"] != today_date:
        user_data[user_id]["used_today"] = 0
        user_data[user_id]["last_used"] = today_date
    
    if user_data[user_id]["used_today"] >= 5:
        update.message.reply_text("❌ الحد الأقصى لعدد الملفات المرسلة في اليوم هو 5 ملفات فقط.")
        return

    document = update.message.document
    if document and document.file_name.lower().endswith('.pdf'):
        # التحقق من إرسال أكثر من ملف في نفس الرسالة
        if len(update.message.document) > 1:
            update.message.reply_text("❌ يمكنك إرسال ملف واحد فقط في المرة.")
            return
        
        if document.file_size > 1 * 1024 * 1024:
            update.message.reply_text("❌ حجم الملف أكبر من 1MB. يرجى إرسال ملف PDF أصغر.")
            return
        # إرسال رسالة التحميل الأولية
        progress_message = update.message.reply_text("⏳ جاري ترجمة الملف، يرجى الانتظار...")

        pdf_path = document.file_name
        output_dir = "converted_files"
        
        # تحميل الملف
        new_file = context.bot.get_file(document.file_id)
        new_file.download(custom_path=pdf_path)
        logger.info("📥 تم تحميل الملف: %s", pdf_path)
        
        # تحويل PDF إلى HTML
        html_path = convert_pdf_to_html(pdf_path, output_dir, update, context, progress_message.message_id)
        if not html_path:
            update.message.reply_text("❌ حدث خطأ أثناء تحويل الملف.")
            return
        
        # ترجمة HTML
        translated_html = translate_html(html_path)
        
        # تحويل HTML المترجم إلى PDF
        translated_pdf = convert_html_to_pdf(translated_html)
        
        if translated_pdf:
            with open(translated_pdf, 'rb') as p_file:
                context.bot.send_document(
                    chat_id=update.message.chat_id, 
                    document=InputFile(p_file),
                    caption="✅ تم تحويل وترجمة الملف بنجاح!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("تعديل على PDF", url="https://t.me/i2pdfbot")]
                    ])
                )
            
            # تحديث عدد الملفات المرسلة
            user_data[user_id]["used_today"] += 1
            save_user_data(user_data)
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
