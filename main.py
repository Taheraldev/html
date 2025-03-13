from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from bs4 import BeautifulSoup
import requests
import io
import logging

# إعدادات المفاتيح
TELEGRAM_TOKEN = "6016945663:AAETwVMU3m27J5lcf7qKlc-90I26ABlY8wA"  # تم إضافة التوكن هنا
MYMEMORY_API_KEY = "c9e7523ff7269bdbb2cc"   # مفتاح MyMemory API

# إعداد التسجيل (للأخطاء)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def translate_text(text: str, source_lang: str = 'en', target_lang: str = 'ar') -> str:
    """ترجمة النص باستخدام MyMemory API."""
    url = "https://api.mymemory.translated.net/get"
    params = {
        'q': text,
        'langpair': f"{source_lang}|{target_lang}",
        'key': MYMEMORY_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # تحقق من الأخطاء
        data = response.json()
        
        if data['responseStatus'] == 200:
            return data['responseData']['translatedText']
        else:
            logger.error(f"Translation error: {data.get('responseDetails', 'Unknown error')}")
            return text
    except Exception as e:
        logger.error(f"API request failed: {e}")
        return text

async def handle_html_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة ملف HTML المرسل."""
    user = update.message.from_user
    document = update.message.document
    
    # تحقق من أن الملف HTML
    if document.mime_type != "text/html" and not document.file_name.endswith('.html'):
        await update.message.reply_text("⚠️ يرجى إرسال ملف HTML صحيح.")
        return
    
    # تنزيل الملف
    file = await context.bot.get_file(document.file_id)
    file_stream = io.BytesIO()
    await file.download_to_memory(out=file_stream)
    file_stream.seek(0)
    html_content = file_stream.read().decode('utf-8')
    
    # تحليل HTML واستخراج النصوص
    soup = BeautifulSoup(html_content, 'html.parser')
    text_nodes = soup.find_all(text=True)
    
    # ترجمة النصوص (تجاهل النصوص داخل <script> و <style>)
    for element in text_nodes:
        if element.parent.name in ['script', 'style', 'meta', 'noscript']:
            continue
        stripped_text = element.strip()
        if stripped_text:
            translated_text = await translate_text(stripped_text)
            element.replace_with(translated_text)
    
    # إعادة بناء HTML المترجم
    translated_html = str(soup)
    
    # إرسال الملف المترجم
    output = io.BytesIO(translated_html.encode('utf-8'))
    output.name = "translated_ar.html"
    await update.message.reply_document(document=InputFile(output), caption="✅ تم الترجمة بنجاح!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب."""
    await update.message.reply_text("مرحبًا! أرسل لي ملف HTML وسأترجمه إلى العربية.")

def main():
    # تشغيل البوت
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # إضافة handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_html_file))
    
    # بدء الاستماع للتحديثات
    application.run_polling()

if __name__ == "__main__":
    main()
