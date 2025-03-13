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

# الحصول على المفاتيح من البيئة
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CLOUDCONVERT_API_KEY = os.getenv('CLOUDCONVERT_API_KEY')

# أمر /start للتعريف بالبوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('مرحبًا! لإستخدام البوت، يُرجى أولاً إرسال أمر /h لتفعيل عملية التحويل.')

# أمر /h لتفعيل وضع تحويل ملفات PDF
async def enable_pdf_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["pdf_mode"] = True
    await update.message.reply_text('تم تفعيل وضع التحويل، الآن يمكنك إرسال ملف PDF.')

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # التحقق من تفعيل الأمر /h
    if not context.user_data.get("pdf_mode"):
        await update.message.reply_text('يرجى إرسال أمر /h أولاً لتفعيل عملية التحويل.')
        return

    if not update.message.document:
        await update.message.reply_text('يرجى إرسال ملف PDF.')
        return

    document = update.message.document

    if document.mime_type != 'application/pdf':
        await update.message.reply_text('الملف ليس بصيغة PDF!')
        return

    # التحقق من حجم الملف (5MB = 5 * 1024 * 1024 بايت)
    if document.file_size > 5 * 1024 * 1024:
        await update.message.reply_text('حجم الملف المرسل يتجاوز الحد الأقصى 5MB.')
        return

    try:
        # إرسال رسالة توضيحية ببدء المعالجة
        await update.message.reply_text('جاري معالجة، انتظر بعض وق...')
        
        # تنزيل الملف المؤقت
        file = await document.get_file()
        _, ext = os.path.splitext(document.file_name)

        with tempfile.TemporaryDirectory() as tmp_dir:
            # حفظ الملف مؤقتًا
            pdf_path = os.path.join(tmp_dir, f'input{ext}')
            await file.download_to_drive(pdf_path)

            # إنشاء مهمة تحويل في CloudConvert
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

            if 'data' not in job or 'tasks' not in job['data']:
                raise Exception('فشل في إنشاء مهمة التحويل')

            # الحصول على معلومات الرفع
            upload_task = next(t for t in job['data']['tasks'] if t['name'] == 'import-1')
            upload_url = upload_task['result']['form']['url']
            upload_fields = upload_task['result']['form']['parameters']

            # رفع الملف إلى CloudConvert
            with open(pdf_path, 'rb') as f:
                requests.post(upload_url, data=upload_fields, files={'file': (document.file_name, f)})

            # الانتظار حتى اكتمال التحويل
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
                    await update.message.reply_text('❌ فشل في عملية التحويل!')
                    return
                await asyncio.sleep(2)

            # تنزيل وتجهيز الملف الناتج
            html_response = requests.get(html_url)
            output_filename = f'converted_{datetime.now().strftime("%Y%m%d%H%M%S")}.html'

            # إرسال الملف الناتج
            await update.message.reply_document(
                document=html_response.content,
                filename=output_filename,
                caption='تم التحويل بنجاح! ✅'
            )
    except Exception as e:
        print(f'Error: {e}')
        await update.message.reply_text('حدث خطأ أثناء المعالجة! ⚠️')
    finally:
        # إزالة علم تحويل PDF لضمان إرسال أمر /h في كل مرة
        context.user_data.pop("pdf_mode", None)

if __name__ == '__main__':
    # تهيئة البوت
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # إضافة handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('h', enable_pdf_mode))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_pdf))

    # بدء البوت
    print('Bot is running...')
    app.run_polling()
