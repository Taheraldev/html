import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعداد متغيرات البيئة
CLOUDCONVERT_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiZDc5OWYxYTJjZjA2NmEyN2M4YmFiZGI0OGVkZjEwZmRiNTRiOGJiNDU3ZWFkZmEzNDQ1MDYxMWZlNmJjMjczOTAyZGM0OTU4YTQ1NzFiMGQiLCJpYXQiOjE3NDE4MTMyNjEuMDcxNDE4LCJuYmYiOjE3NDE4MTMyNjEuMDcxNDE5LCJleHAiOjQ4OTc0ODY4NjEuMDYzMDcxLCJzdWIiOiI3MTMxNzE4OCIsInNjb3BlcyI6WyJ0YXNrLnJlYWQiLCJ0YXNrLndyaXRlIiwid2ViaG9vay5yZWFkIiwid2ViaG9vay53cml0ZSIsInByZXNldC5yZWFkIiwicHJlc2V0LndyaXRlIl19.IhQ5aT5YCN4V8rygowdv4eFRDUGpvvSV8CjJih2Bq0sTTkangZKp3RVW4ncdETOaBpTj1diiFZJDZlcJcoOkM2glgkpzaACCg3ODu2US79gYyWS4aR_jMfuaSzBAcjQxhIpW4AVMCp_-QBA-lO0ev1Gje9KRfjUrRbi-kt9T9f-gi7aY4vEcxUE40-PTFl9L7NVWtOntZngwSPb1478_CO4OCuq8E-SbQkyAdDDSJ_ipiVePeZQWlIRvlLOhn8fQ_bRdC022SkIgkzpJny0c-55lAYid5Q8oWBbW4AgeskTNsbPJouxeUFwtdhcnprrQL7-sQ7_U10WXWUdWBomDaQbcf4toQ8AKQRIPLMhaxmiiCACoVcF7CLLP0G4EHx1Dsml--zyLVrxvL3qudIaw3akOZNWPutu2exrlO9dUV2RYynS7WKQQjlP_ARLYQ1YfKUIYFEhVM_p6NEDKjI-91Nt7Cba_rYLoFrUbFu9OrSC2oUUSvZZxnmUsLAFYTiTfIH_eEcHT2FzAolwlA_r5T6579A5HCHmt_ckZpiUEuPzMHKf3Zx4wlteIKT1gYyTq0TNf8jf4WLUqPF_DSFqyQaujfD_r_KMhkc2P2uCmx7nI6fEHbXrP1wTeTz_CX21vk5BhmssFlBqhP9-55KR4jEGwf1hNQah-isAgk-v8x1Y"
TELEGRAM_BOT_TOKEN = "6334414905:AAGdBEBDfiY7W9Nhyml1wHxSelo8gfpENR8"

# تحميل ملف PDF ومعالجته
def convert_pdf_to_html(file_path):
    url = "https://api.cloudconvert.com/v2/convert"
    headers = {
        "Authorization": f"Bearer {CLOUDCONVERT_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "tasks": {
            "import-1": {
                "operation": "import/upload"
            },
            "convert-1": {
                "operation": "convert",
                "input": "import-1",
                "output_format": "html"
            },
            "export-1": {
                "operation": "export/url",
                "input": "convert-1"
            }
        }
    }

    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 201:
        task_id = response.json()["data"]["id"]
        return task_id
    else:
        return None

# استقبال الملفات من المستخدم
def handle_document(update: Update, context: CallbackContext):
    file = update.message.document
    if file.mime_type == "application/pdf":
        file_path = f"{file.file_id}.pdf"
        file.get_file().download(file_path)

        update.message.reply_text("جارٍ تحويل الملف، يرجى الانتظار...")
        task_id = convert_pdf_to_html(file_path)

        if task_id:
            update.message.reply_text(f"تم إرسال الملف للتحويل، تابع هنا: https://cloudconvert.com/dashboard/tasks/{task_id}")
        else:
            update.message.reply_text("حدث خطأ أثناء التحويل، حاول مرة أخرى.")

        os.remove(file_path)
    else:
        update.message.reply_text("الرجاء إرسال ملف PDF فقط.")

# إعداد البوت
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.document, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
