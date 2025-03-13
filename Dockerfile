# استخدم صورة Python الرسمية
FROM python:3.10-slim

# تعيين متغير البيئة لعدم إنشاء ملفات Python bytecode
ENV PYTHONUNBUFFERED=1

# تثبيت المتطلبات الأساسية
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libpoppler-cpp-dev \
    poppler-utils \
    wget \
    && rm -rf /var/lib/apt/lists/*

# إنشاء مجلد للتطبيق
WORKDIR /app

# نسخ ملفات التطبيق
COPY . .

# تحديث pip
RUN pip install --upgrade pip

# تثبيت المتطلبات من ملف requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# تشغيل البوت
CMD ["python", "main.py"]
