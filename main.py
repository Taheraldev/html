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

# الحصول على المفاتيح من البيئة
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CLOUDCONVERT_API_KEY = os.getenv('CLOUDCONVERT_API_KEY')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'مرحبًا! 👋\n'
        'أرسل لي ملف PDF وسأقوم ب:\n'
        '1. تحويله إلى HTML\n'
        '2. ترجمة المحتوى إلى العربية\n'
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
        # تنزيل الملف
        file = await document.get_file()
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # حفظ الملف PDF مؤقتًا
            pdf_path = os.path.join(tmp_dir, 'input.pdf')
            await file.download_to_drive(pdf_path)
            
            # تحويل PDF إلى HTML
            original_html_path = await convert_pdf_to_html(pdf_path, tmp_dir)
            
            # ترجمة HTML إلى العربية
            translated_html_path = os.path.join(tmp_dir, 'translated.html')
            await translate_html(original_html_path, translated_html_path)
            
            # إرسال النتائج
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            await update.message.reply_document(
                document=open(original_html_path, 'rb'),
                filename=f'original_{timestamp}.html',
                caption='النسخة الأصلية (الإنجليزية)'
            )
            await update.message.reply_document(
                document=open(translated_html_path, 'rb'),
                filename=f'translated_{timestamp}.html',
                caption='النسخة المترجمة (العربية)'
            )

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
    """ترجمة محتوى HTML باستخدام deep_translator"""
    with open(input_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    translator = GoogleTranslator(source='en', target='ar')
    
    # ترجمة جميع النصوص
    for element in soup.find_all(text=True):
        if element.parent.name in ['script', 'style', 'meta']:
            continue
        try:
            translated = translator.translate(element.strip())
            element.replace_with(translated)
        except Exception as e:
            print(f"Translation error: {e}")
            continue
    
    # حفظ الملف المترجم
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_pdf))
    print('✅ البوت يعمل...')
    app.run_polling()
