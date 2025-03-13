# استخدام صورة رسمية لـ Python
FROM python:3.10-slim

# تعيين المجلد الافتراضي داخل الحاوية
WORKDIR /app

# تثبيت المتطلبات الأساسية (Poppler-utils لتحويل PDF إلى HTML)
RUN apt-get update && \
    apt-get install -y wget gnupg && \
    # إضافة مستودع pdf2htmlEX
    wget -qO - https://github.com/coolwanglu/pdf2htmlEX/releases/download/v0.18.8/pdf2htmlEX-0.18.8-linux-x86_64.tar.bz2 | tar -xj -C /usr/local/bin/ && \
    # تنظيف الحزم غير المستخدمة
    rm -rf /var/lib/apt/lists/*

# نسخ ملفات المشروع إلى الحاوية
COPY . /app

# تثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir -r requirements.txt

# تحديد الأمر لتشغيل البوت
CMD ["python", "bot.py"]
