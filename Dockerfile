# استخدام صورة أساسية تحتوي على Python
FROM python:3.9-slim

# إعداد المتغيرات البيئية لتجنب تفاعلات apt
ENV DEBIAN_FRONTEND=noninteractive

# تثبيت التبعيات اللازمة
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libfontconfig1-dev \
    libpoppler-cpp-dev \
    libpoppler-private-dev \
    libpng-dev \
    libjpeg-dev \
    libssl-dev \
    libx11-dev \
    libxext-dev \
    libxi-dev \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# استنساخ وبناء pdf2htmlEX من المصدر
RUN git clone --depth 1 https://github.com/coolwanglu/pdf2htmlEX.git /opt/pdf2htmlEX \
    && cd /opt/pdf2htmlEX \
    && cmake . \
    && make -j$(nproc) \
    && make install

# نسخ ملفات التطبيق وتثبيت تبعيات Python
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# تشغيل التطبيق (قم بتعديل الأمر بما يناسب تطبيقك)
CMD ["python", "main.py"]
