import os
import asyncio
import tempfile
from python_telegram_bot import Application, MessageHandler, filters
import requests
from datetime import datetime

# احصل على المفاتيح من البيئة
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CLOUDCONVERT_API_KEY = os.getenv('CLOUDCONVERT_API_KEY')

async def handle_pdf(update, context):
    user = update.message.from_user
    document = update.message.document

    # التحقق من نوع الملف
    if document.mime_type != 'application/pdf':
        await update.message.reply_text('يرجى إرسال ملف PDF فقط.')
        return

    # تنزيل الملف
    file = await context.bot.get_file(document.file_id)
    _, ext = os.path.splitext(document.file_name)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_path = os.path.join(tmp_dir, f'input{ext}')
        await file.download_to_drive(pdf_path)
        
        # إعداد معلمات التحويل
        job_data = {
            "tasks": {
                "import-1": {
                    "operation": "import/upload"
                },
                "task-1": {
                    "operation": "convert",
                    "input": ["import-1"],
                    "input_format": "pdf",
                    "output_format": "html"
                },
                "export-1": {
                    "operation": "export/url",
                    "input": ["task-1"]
                }
            }
        }

        # إنشاء مهمة تحويل
        headers = {'Authorization': f'Bearer {CLOUDCONVERT_API_KEY}'}
        response = requests.post('https://api.cloudconvert.com/v2/jobs', json=job_data, headers=headers)
        job = response.json()
        
        # الحصول على رابط التحميل
        upload_task = next(t for t in job['data']['tasks'] if t['name'] == 'import-1')
        upload_url = upload_task['result']['form']['url']
        upload_fields = upload_task['result']['form']['parameters']
        
        # رفع الملف إلى CloudConvert
        with open(pdf_path, 'rb') as f:
            files = {'file': (document.file_name, f)}
            requests.post(upload_url, data=upload_fields, files=files)
        
        # الانتظار حتى اكتمال التحويل
        export_task = next(t for t in job['data']['tasks'] if t['name'] == 'export-1')
        while True:
            task_response = requests.get(f'https://api.cloudconvert.com/v2/tasks/{export_task["id"]}', headers=headers)
            task_data = task_response.json()['data']
            if task_data['status'] == 'finished':
                html_url = task_data['result']['files'][0]['url']
                break
            elif task_data['status'] == 'error':
                await update.message.reply_text('فشل التحويل. يرجى المحاولة بملف آخر.')
                return
            await asyncio.sleep(2)

        # تنزيل ملف HTML
        html_response = requests.get(html_url)
        html_path = os.path.join(tmp_dir, 'output.html')
        with open(html_path, 'wb') as f:
            f.write(html_response.content)
        
        # إرسال النتيجة
        await update.message.reply_document(
            document=open(html_path, 'rb'),
            filename=f'converted_{datetime.now().strftime("%Y%m%d%H%M%S")}.html'
        )

if __name__ == '__main__':
    # إعداد البوت
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # إضافة handler للملفات
    application.add_handler(MessageHandler(filters.Document.ALL, handle_pdf))
    
    # تشغيل البوت
    application.run_polling()
