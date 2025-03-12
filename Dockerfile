# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# تثبيت الاعتميات النظامية (مهم للخطوط العربية ومعالجة النصوص)
RUN apt-get update && apt-get install -y \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    fonts-noto \          # للخطوط العربية الأساسية
    && rm -rf /var/lib/apt/lists/*

# نسخ الملفات المطلوبة
COPY requirements.txt .
COPY main.py .

# تثبيت حزم بايثون
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# تشغيل البوت
CMD ["python", "main.py"]
