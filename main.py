import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext

# تحميل المتغيرات من ملف .env
load_dotenv()
CLOUDCONVERT_API_KEY = os.getenv("CLOUDCONVERT_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# التحقق من أن المفاتيح تم تحميلها
if not CLOUDCONVERT_API_KEY or not TELEGRAM_BOT_TOKEN:
    raise ValueError("يرجى التأكد من إعداد ملف .env بشكل صحيح.")

# تحويل ملف PDF إلى HTML باستخدام CloudConvert
def convert_pdf_to_html(file_path):
    url = "https://api.cloudconvert.com/v2/convert"
    headers = {"Authorization": f"Bearer {CLOUDCONVERT_API_KEY}", "Content-Type": "application/json"}
    data = {
        "tasks": {
            "import-1": {"operation": "import/upload"},
            "convert-1": {"operation": "convert", "input": "import-1", "output_format": "html"},
            "export-1": {"operation": "export/url", "input": "convert-1"}
        }
    }

    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 201:
        task_id = response.json()["data"]["id"]
        return task_id
    else:
        return None

# استقبال الملفات من المستخدم
async def handle_document(update: Update, context: CallbackContext):
    file = update.message.document
    if file.mime_type == "application/pdf":
        file_path = f"{file.file_id}.pdf"

        # الحصول على الملف من تيليجرام ثم تحميله
        telegram_file = await file.get_file()
        await telegram_file.download_to_drive(file_path)

        await update.message.reply_text("جارٍ تحويل الملف، يرجى الانتظار...")
        task_id = convert_pdf_to_html(file_path)

        if task_id:
            await update.message.reply_text(f"تم إرسال الملف للتحويل، تابع هنا: https://cloudconvert.com/dashboard/tasks/{task_id}")
        else:
            await update.message.reply_text("حدث خطأ أثناء التحويل، حاول مرة أخرى.")

        os.remove(file_path)
    else:
        await update.message.reply_text("الرجاء إرسال ملف PDF فقط.")

# إعداد البوت
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("🤖 البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
