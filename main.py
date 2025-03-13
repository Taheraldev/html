from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from bs4 import BeautifulSoup
import requests
import io
import logging


TELEGRAM_TOKEN = "6334414905:AAFK59exfc4HuQQJdxk-mwONn5K4yODCIJg"
MYMEMORY_API_KEY = "7dfa552fac8aad334ae1"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def translate_text(text: str, source_lang: str = 'en', target_lang: str = 'ar') -> str:
    url = "https://api.mymemory.translated.net/get"
    params = {
        'q': text,
        'langpair': f"{source_lang}|{target_lang}",
        'key': MYMEMORY_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
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
    user = update.message.from_user
    document = update.message.document
    
    # التحقق من نوع الملف
    if document.mime_type != "text/html" and not document.file_name.endswith('.html'):
        await update.message.reply_text("⚠️ يرجى إرسال ملف HTML صحيح.")
        return
    
    # التحقق من حجم الملف
    max_size = 2 * 1024 * 1024  # 2MB
    if document.file_size > max_size:
        await update.message.reply_text("⚠️ حجم الملف يتجاوز الحد المسموح (2MB).")
        return
    
    # إرسال رسالة الانتظار
    processing_msg = await update.message.reply_text("⏳ تجري عملية الترجمة، الرجاء الانتظار...")
    
    try:
        # تنزيل الملف
        file = await context.bot.get_file(document.file_id)
        file_stream = io.BytesIO()
        await file.download_to_memory(out=file_stream)
        file_stream.seek(0)
        html_content = file_stream.read().decode('utf-8')
        
        # معالجة وترجمة المحتوى
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for element in soup.find_all(string=True):
            if element.parent.name in ['script', 'style', 'meta', 'noscript']:
                continue
            stripped_text = element.strip()
            if stripped_text:
                translated_text = await translate_text(stripped_text)
                element.replace_with(translated_text)
        
        translated_html = str(soup)
        
        # إرسال الملف المترجم
        output = io.BytesIO(translated_html.encode('utf-8'))
        output.name = "translated_ar.html"
        await update.message.reply_document(
            document=InputFile(output),
            caption="✅ تم الترجمة بنجاح!\nقم بإعادة توجيه هذا الملف للبوت الرئيسي لتحويله إلى PDF: @i2pdfbot \n@ta_ja199 للاستفسار"
        )
        
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء المعالجة. يرجى المحاولة لاحقًا.")
        
    finally:
        # حذف رسالة الانتظار بعد الانتهاء
        await context.bot.delete_message(chat_id=update.message.chat_id, message_id=processing_msg.message_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحبًا! أرسل لي ملف HTML (بحد أقصى 2MB) وسأترجمه إلى العربية.\n"
        "بوت تابع لـ @i2pdfbot \n"
        "المطور: @ta_ja199"
    )

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_html_file))
    
    application.run_polling()

if __name__ == "__main__":
    main()
