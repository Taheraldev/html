import os
from telegram import Update
from telegram.ext import (
    Application,  # تم استبدال Updater بـ Application
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from bs4 import BeautifulSoup
from googletrans import Translator

# استبدل 'TOKEN' بالتوكن الخاص ببوتك
TOKEN = "6016945663:AAGf2B4dpCo-nVFNXbyPUHuS9XwA1ugGa4Y"
translator = Translator()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('مرحبا! أرسل لي ملف HTML وسأقوم بترجمته إلى العربية مع الحفاظ على التنسيق.')

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # تحميل الملف
        file = await update.message.document.get_file()
        filename = update.message.document.file_name
        
        if not filename.lower().endswith('.html'):
            await update.message.reply_text('يرجى إرسال ملف HTML فقط.')
            return
            
        downloaded_file = await file.download_to_drive()
        
        # قراءة الملف
        with open(downloaded_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # تحليل HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # ترجمة النص مع الحفاظ على الهيكل
        def translate_text(element):
            if element.string and element.string.strip():
                try:
                    translated = translator.translate(element.string, src='en', dest='ar').text
                    element.string.replace_with(translated)
                except:
                    pass  # تجاهل الأخطاء في حال وجودها
        
        for element in soup.find_all(text=True):
            if element.parent.name not in ['script', 'style', 'meta', 'noscript']:
                translate_text(element)
        
        # حفظ الملف المترجم
        translated_html = soup.prettify()
        output_filename = f"translated_{filename}"
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(translated_html)
        
        # إرسال الملف المترجم
        await update.message.reply_document(document=open(output_filename, 'rb'))
        
        # تنظيف الملفات المؤقتة
        os.remove(downloaded_file)
        os.remove(output_filename)
        
    except Exception as e:
        await update.message.reply_text(f'حدث خطأ: {str(e)}')

def main():
    # إنشاء Application بدلاً من Updater
    application = Application.builder().token(TOKEN).build()
    
    # إضافة handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # بدء البوت
    application.run_polling()

if __name__ == '__main__':
    main()
