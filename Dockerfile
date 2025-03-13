# استخدام صورة جاهزة تحتوي على pdf2htmlEX مثبتة بالفعل
FROM jrottenberg/ffmpeg:4.3-ubuntu

# تثبيت الأدوات اللازمة مثل wget و python3
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-dev wget gnupg

# تثبيت المكتبات المطلوبة
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install --no-cache-dir -r requirements.txt

# نسخ الملفات الخاصة بالبوت إلى الحاوية
COPY . /app

# تحديد الأمر لتشغيل البوت
CMD ["python3", "bot.py"]
