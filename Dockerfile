# استخدام صورة بايثون الأساسية
FROM python:3.9-slim

# تعيين متغير البيئة لتجنب التفاعلات أثناء التثبيت
ENV DEBIAN_FRONTEND=noninteractive

# تثبيت الأدوات والتبعيات المطلوبة
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# تحديد مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملفات المشروع
COPY requirements.txt .

# تثبيت المكتبات المطلوبة لبايثون
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع
COPY . .

# تشغيل البوت عند بدء الحاوية
CMD ["python", "main.py"]
