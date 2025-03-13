# استخدام صورة رسمية لـ Python
FROM python:3.10-slim

# تعيين المجلد الافتراضي داخل الحاوية
WORKDIR /app

# تثبيت المتطلبات الأساسية (Poppler-utils لتحويل PDF إلى HTML)
RUN apt-get update && apt-get install -y poppler-utils pdf2htmlEX && rm -rf /var/lib/apt/lists/*

# نسخ ملفات المشروع إلى الحاوية
COPY . /app

# تثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir -r requirements.txt

# تحديد الأمر لتشغيل البوت
CMD ["python", "bot.py"]
