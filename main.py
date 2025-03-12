import os
import asyncio
import tempfile
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# المتغيرات البيئية
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CLOUDCONVERT_API_KEY = os.getenv('CLOUDCONVERT_API_KEY')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'مرحبًا! 🚀\n'
        'أرسل ملف PDF وسأقوم ب:\n'
        '1. تحويله إلى HTML\n'
        '2. ترجمة المحتوى للعربية\n'
        '3. إرسال النسختين معًا'
    )

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document:
        await update.message.reply_text('❗ يرجى إرسال ملف PDF.')
        return

    document = update.message.document
    
    if document.mime_type != 'application/pdf':
        await update.message.reply_text('❌ الملف ليس بصيغة PDF!')
        return

    try:
        file = await document.get_file()
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = os.path.join(tmp_dir, 'input.pdf')
            await file.download_to_drive(pdf_path)
            
            original_html_path = await convert_pdf_to_html(pdf_path, tmp_dir)
            translated_html_path = os.path.join(tmp_dir, 'translated.html')
            await translate_html(original_html_path, translated_html_path)
            
            await send_results(update, original_html_path, translated_html_path)

    except Exception as e:
        print(f'Error: {e}')
        await update.message.reply_text('⚠️ حدث خطأ أثناء المعالجة!')

async def convert_pdf_to_html(pdf_path: str, output_dir: str) -> str:
    """تحويل PDF إلى HTML باستخدام CloudConvert"""
    job_data = {
        "tasks": {
            "import-1": {"operation": "import/upload"},
            "task-1": {
                "operation": "convert",
                "input": ["import-1"],
                "input_format": "pdf",
                "output_format": "html"
            },
            "export-1": {"operation": "export/url", "input": ["task-1"]}
        }
    }
    
    headers = {'Authorization': f'Bearer {CLOUDCONVERT_API_KEY}'}
    response = requests.post('https://api.cloudconvert.com/v2/jobs', json=job_data, headers=headers)
    job = response.json()
    
    if 'data' not in job:
        raise Exception('CloudConvert API Error')
    
    # رفع الملف
    upload_task = next(t for t in job['data']['tasks'] if t['name'] == 'import-1')
    upload_url = upload_task['result']['form']['url']
    upload_fields = upload_task['result']['form']['parameters']
    
    with open(pdf_path, 'rb') as f:
        requests.post(upload_url, data=upload_fields, files={'file': ('input.pdf', f)})
    
    # انتظار التحويل
    export_task = next(t for t in job['data']['tasks'] if t['name'] == 'export-1')
    while True:
        task_response = requests.get(
            f'https://api.cloudconvert.com/v2/tasks/{export_task["id"]}',
            headers=headers
        )
        task_data = task_response.json()['data']
        
        if task_data['status'] == 'finished':
            html_url = task_data['result']['files'][0]['url']
            break
        elif task_data['status'] in ['error', 'cancelled']:
            raise Exception('فشل التحويل')
        await asyncio.sleep(2)
    
    # تنزيل HTML
    html_response = requests.get(html_url)
    output_path = os.path.join(output_dir, 'original.html')
    with open(output_path, 'wb') as f:
        f.write(html_response.content)
    
    return output_path

async def translate_html(input_path: str, output_path: str):
    """ترجمة المحتوى مع إصلاح التشويش العربي"""
    with open(input_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html5lib')
    translator = GoogleTranslator(source='en', target='ar')
    
    # إعداد هيكل HTML عربي
    if not soup.find('meta', {'charset': 'UTF-8'}):
        meta_charset = soup.new_tag('meta', charset='UTF-8')
        soup.head.insert(0, meta_charset)
    
    if soup.html:
        soup.html['dir'] = 'rtl'
        soup.html['lang'] = 'ar'
    
    # إضافة CSS للخطوط العربية
    style_tag = soup.new_tag('style')
    style_tag.string = '''
        body {
            font-family: 'Noto Sans Arabic', 'Arial', sans-serif;
            line-height: 1.8;
            text-align: right;
            direction: rtl;
            unicode-bidi: bidi-override;  # إصلاح اتجاه النص
        }
        p, h1, h2, h3, h4, h5, h6 {
            margin: 10px 0;
            padding: 0;
        }
    '''
    soup.head.append(style_tag)
    
    # ترجمة النصوص
    for element in soup.find_all(string=True):
        if element.parent.name in ['script', 'style', 'meta']:
            continue
        try:
            cleaned_text = element.strip()
            if cleaned_text:
                translated = translator.translate(cleaned_text)
                element.replace_with(translated)
        except Exception as e:
            print(f"Translation error: {e}")
            continue
    
    # الحفظ النهائي
    with open(output_path, 'w', encoding='utf-8', errors='xmlcharrefreplace') as f:
        f.write(str(soup))

async def send_results(update: Update, original_path: str, translated_path: str):
    """إرسال الملفات النهائية"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    await update.message.reply_document(
        document=open(original_path, 'rb'),
        filename=f'original_{timestamp}.html',
        caption='النسخة الأصلية (الإنجليزية)'
    )
    
    await update.message.reply_document(
        document=open(translated_path, 'rb'),
        filename=f'translated_{timestamp}.html',
        caption='النسخة المترجمة (العربية)'
    )

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_pdf))
    print('✅ البوت يعمل...')
    app.run_polling(allowed_updates=Update.ALL_TYPES)  # إضافة allowed_updates
