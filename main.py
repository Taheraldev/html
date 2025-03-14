import os
import subprocess
import logging
import datetime
import json
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from bs4 import BeautifulSoup
from googletrans import Translator
import PyPDF2

# إعداد تسجيل الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إعداد المترجم
translator = Translator()

# متغيرات البيئة
ADMIN_ID = os.getenv("ADMIN_ID", "5198110160")
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ملف بيانات المستخدمين لتخزين المستخدمين الذين ضغطوا /start
USER_FILE = "user_data.json"

# متغير لتتبع عدد الملفات لكل مستخدم في اليوم (الحد الأقصى 5 ملفات)
user_file_count = {}

def get_progress_bar(percentage: int) -> str:
    """
    دالة تقوم بإنشاء شريط تقدم باستخدام مربعات.
    العدد الكلي للمربعات هو 5:
      - المربع الممتلئ: ◼️
      - المربع الفارغ: ◻️
    """
    total_blocks = 5
    filled_blocks = int(percentage / 20)
    return "".join(["◼️" for _ in range(filled_blocks)] + ["◻️" for _ in range(total_blocks - filled_blocks)])

def load_user_data() -> set:
    """تحميل بيانات المستخدمين من ملف JSON وإرجاعها كمجموعة."""
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return set(data) if isinstance(data, list) else set()
        except Exception as e:
            logger.error("❌ خطأ أثناء تحميل بيانات المستخدمين: %s", e)
            return set()
    return set()

def save_user_data(users: set):
    """حفظ بيانات المستخدمين في ملف JSON."""
    try:
        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump(list(users), f)
    except Exception as e:
        logger.error("❌ خطأ أثناء حفظ بيانات المستخدمين: %s", e)

def start(update: Update, context: CallbackContext):
    """رسالة الترحيب عند بدء البوت وإرسال إشعار للمشرف للمستخدم الجديد فقط."""
    user = update.message.from_user
    start_message = (
        "مرحبا انا بوت اقوم بترجمة ملفات pdf \n"
        "البوت تابع ل: @i2pdfbot \n"
        "😇 ملاحضه البوت تجريبي فقط سوف يتم تطويره قريبا \n"
        "@ta_ja199 لاستفسار"
    )
    
    # إعداد الأزرار المدمجة
    keyboard = [
        [InlineKeyboardButton("قناة البوت 🔫", url="https://t.me/i2pdfbotchannel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(start_message, reply_markup=reply_markup)
    
    # تحميل بيانات المستخدمين من الملف
    known_users = load_user_data()
    # إرسال إشعار للمشرف فقط إذا كان المستخدم جديداً
    if user.id not in known_users:
        known_users.add(user.id)
        save_user_data(known_users)
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
    # إنشاء ملف HTML مترجم جديد مع لاحقة _translated
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
    """معالجة ملف PDF المرسل من المستخدم مع تحديث نسبة التقدم وإدخال القيود المطلوبة."""
    # منع إرسال أكثر من ملف في دفعة واحدة
    if update.message.media_group_id is not None:
        update.message.reply_text("❌ الرجاء إرسال ملف واحد فقط في كل مرة.\n الا وسف يتم حظرك😂")
        return

    document = update.message.document
    if document and document.file_name.lower().endswith('.pdf'):
        if document.file_size > 1 * 1024 * 1024:
            update.message.reply_text("❌ حجم الملف أكبر من 1MB. يرجى إرسال ملف PDF أصغر.\n قسم بضغط ملف في البوت هذا :@i2pdfbot\n ثم قم بارسال ملف لكي اترجمة")
            return

        # إرسال رسالة البداية مع نسبة التقدم (0%)
        percentage = 0
        progress_text = f"⏳ جاري ترجمة الملف، يرجى الانتظار... ({percentage}%)\n{get_progress_bar(percentage)}"
        progress_message = update.message.reply_text(progress_text)

        # التحقق من عدد الملفات المرسلة لهذا المستخدم اليوم (الحد الأقصى 5 ملفات)
        user_id = update.message.from_user.id
        today = datetime.date.today()
        if user_id in user_file_count:
            if user_file_count[user_id]['date'] != today:
                user_file_count[user_id]['date'] = today
                user_file_count[user_id]['count'] = 0
        else:
            user_file_count[user_id] = {'date': today, 'count': 0}
        
        if user_file_count[user_id]['count'] >= 5:
            context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=progress_message.message_id,
                text="🚫 لقد تجاوزت الحد الأقصى (5 ملفات يوميًا). يرجى المحاولة غدًا."
            )
            return

        # تحميل الملف
        pdf_path = document.file_name
        output_dir = "converted_files"
        new_file = context.bot.get_file(document.file_id)
        new_file.download(custom_path=pdf_path)
        logger.info("📥 تم تحميل الملف: %s", pdf_path)
        percentage = 20
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=progress_message.message_id,
            text=f"⏳ جاري تحويل وترجمة الملف، يرجى الانتظار... ({percentage}%)\n{get_progress_bar(percentage)}"
        )

        # التحقق من عدد صفحات ملف PDF (الحد الأقصى 5 صفحات)
        try:
            with open(pdf_path, "rb") as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                num_pages = len(reader.pages)
            if num_pages > 5:
                context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=progress_message.message_id,
                    text="❌ الحد الأقصى هو 5 صفحات بسبب التحميل الزائد.\n قسم بتقسيم ملف في البوت هذا :@i2pdfbot\n ثم قم بارسال ملف لكي اترجمة"
                )
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                return
        except Exception as e:
            logger.error("❌ خطأ أثناء قراءة ملف PDF: %s", e)
            context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=progress_message.message_id,
                text="❌ حدث خطأ أثناء قراءة ملف PDF."
            )
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            return

        # تحويل PDF إلى HTML
        html_path = convert_pdf_to_html(pdf_path, output_dir)
        if not html_path:
            context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=progress_message.message_id,
                text="❌ حدث خطأ أثناء تحويل الملف إلى HTML."
            )
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            return

        percentage = 40
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=progress_message.message_id,
            text=f"⏳ جاري ترجمة الملف، يرجى الانتظار... ({percentage}%)\n{get_progress_bar(percentage)}"
        )

        # ترجمة HTML (يُنشأ ملف مترجم مع لاحقة _translated)
        translated_html = translate_html(html_path)
        percentage = 60
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=progress_message.message_id,
            text=f"⏳ جاري ترجمة الملف، يرجى الانتظار... ({percentage}%)\n{get_progress_bar(percentage)}"
        )

        # تحويل HTML المترجم إلى PDF
        translated_pdf = convert_html_to_pdf(translated_html)
        if not translated_pdf:
            context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=progress_message.message_id,
                text="❌ حدث خطأ أثناء تحويل HTML إلى PDF."
            )
            return

        percentage = 80
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=progress_message.message_id,
            text=f"⏳ جاري ترجمة الملف، يرجى الانتظار... ({percentage}%)\n{get_progress_bar(percentage)}"
        )

        # زيادة عدد الملفات المرسلة لهذا المستخدم
        user_file_count[user_id]['count'] += 1

        # إنشاء زر "✏️ تعديل على PDF" للملف الناتج
        keyboard = [
            [InlineKeyboardButton("✏️ تعديل على PDF", url="https://t.me/i2pdfbot")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # إرسال ملف PDF النهائي مع زر أسفله
        with open(translated_pdf, 'rb') as p_file:
            context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=InputFile(p_file),
                caption="✅ تم ترجمة الملف بنجاح!\n اذا لم يعجيك تصميم استعمل البوت الثاني:@i2pdf2tbot",
                reply_markup=reply_markup
            )
        percentage = 100
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=progress_message.message_id,
            text=f"✅ تم ترجمة الملف بنجاح!\n اذا لم يعجيك تصميم استعمل البوت الثاني:@i2pdf2tbot ({percentage}%)\n{get_progress_bar(percentage)}"
        )
        
        # حذف رسالة الانتظار بعد إرسال الملف النهائي
        context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=progress_message.message_id
        )

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
