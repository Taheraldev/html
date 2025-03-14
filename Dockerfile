# استخدم صورة Python الرسمية
FROM python:3.10-slim

# تثبيت الأدوات المطلوبة، بما في ذلك pdftohtml
RUN apt-get update && apt-get install -y \
    poppler-utils \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# تحديد مجلد العمل
WORKDIR /app

# نسخ الملفات إلى الحاوية
COPY . /app

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r requirements.txt

# تشغيل البوت
CMD ["python", "main.py"]
