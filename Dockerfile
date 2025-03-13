# استخدام صورة رسمية لـ Python
FROM python:3.10-slim

# تعيين المجلد الافتراضي داخل الحاوية
WORKDIR /app

# تثبيت الأدوات المطلوبة بما في ذلك pdftohtml
RUN apt-get update && \
    apt-get install -y poppler-utils python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# نسخ ملفات المشروع إلى الحاوية
COPY . /app

# تثبيت المكتبات المطلوبة
RUN pip3 install --no-cache-dir -r requirements.txt

# تحديد الأمر لتشغيل البوت
CMD ["python3", "main.py"]
