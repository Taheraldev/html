# استخدام صورة Python الكاملة بدلاً من slim
FROM python:3.10

# تعيين المجلد الافتراضي داخل الحاوية
WORKDIR /app

# تثبيت المتطلبات الأساسية وتبعيات البناء
RUN apt-get update && \
    apt-get install -y \
    wget \
    build-essential \
    cmake \
    libpoppler-glib-dev \
    poppler-utils \
    libfontforge-dev \
    pkg-config \
    libspiro-dev \
    python3-dev \
    libjpeg-dev \
    libtiff-dev \
    libpng-dev \
    libgif-dev \
    libxt-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libpangocairo-1.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

# تنزيل وتثبيت pdf2htmlEX من المصدر
RUN wget https://github.com/coolwanglu/pdf2htmlEX/archive/refs/tags/v0.18.8.tar.gz -O pdf2htmlEX.tar.gz \
    && tar -xzf pdf2htmlEX.tar.gz \
    && mkdir pdf2htmlEX-0.18.8/build \
    && cd pdf2htmlEX-0.18.8/build \
    && cmake .. \
    && make \
    && make install \
    && cd /app \
    && rm -rf pdf2htmlEX.tar.gz pdf2htmlEX-0.18.8

# نسخ ملفات المشروع إلى الحاوية
COPY . /app

# تثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir -r requirements.txt

# تحديد الأمر لتشغيل البوت
CMD ["python", "bot.py"]
