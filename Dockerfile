# استخدام صورة رسمية لـ Python
FROM python:3.10-slim

# تعيين المجلد الافتراضي داخل الحاوية
WORKDIR /app

# تثبيت المتطلبات الأساسية (Poppler-utils لتحويل PDF إلى HTML)
RUN apt-get update && \
    apt-get install -y wget gnupg && \
    # تنزيل ملف pdf2htmlEX
    wget https://github.com/coolwanglu/pdf2htmlEX/releases/download/v0.18.8/pdf2htmlEX-0.18.8-linux-x86_64.tar.bz2 && \
    # فك ضغط الملف
    tar -xjvf pdf2htmlEX-0.18.8-linux-x86_64.tar.bz2 && \
    # نقل الملف إلى /usr/local/bin/
    mv pdf2htmlEX-0.18.8-linux-x86_64/pdf2htmlEX /usr/local/bin/ && \
    # تنظيف الحزم غير المستخدمة
    rm -rf /var/lib/apt/lists/* pdf2htmlEX-0.18.8-linux-x86_64.tar.bz2 pdf2htmlEX-0.18.8-linux-x86_64

# نسخ ملفات المشروع إلى الحاوية
COPY . /app

# تثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir -r requirements.txt

# تحديد الأمر لتشغيل البوت
CMD ["python", "bot.py"]
