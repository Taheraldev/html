FROM python:3.10-slim

WORKDIR /app

# تثبيت الاعتميات النظامية
RUN apt-get update && apt-get install -y \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    fonts-noto \
    && rm -rf /var/lib/apt/lists/*

# نسخ الملفات
COPY requirements.txt .
COPY main.py .

# تثبيت الحزم
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# تشغيل البوت
CMD ["python", "main.py"]
