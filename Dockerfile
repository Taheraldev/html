# استخدام صورة رسمية لـ Python
FROM python:3.10-slim

# تعيين المجلد الافتراضي داخل الحاوية
WORKDIR /app

# تثبيت المتطلبات الأساسية (Poppler-utils لتحويل PDF إلى HTML)
RUN apt-get update && \
    apt-get install -y wget gnupg build-essential && \
    # تحميل وتثبيت pdf2htmlEX من المصدر
    wget https://github.com/coolwanglu/pdf2htmlEX/archive/refs/tags/v0.18.8.tar.gz && \
    tar -xzvf v0.18.8.tar.gz && \
    cd pdf2htmlEX-0.18.8 && \
    make && make install && \
    # تنظيف الملفات المؤقتة
    rm -rf /var/lib/apt/lists/* v0.18.8.tar.gz pdf2htmlEX-0.18.8

# نسخ ملفات المشروع إلى الحاوية
COPY . /app

# تثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir -r requirements.txt

# تحديد الأمر لتشغيل البوت
CMD ["python", "bot.py"]
