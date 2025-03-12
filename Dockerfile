FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir python-telegram-bot==20.6 && \
    pip install --no-cache-dir requests==2.31.0 && \
    pip install --no-cache-dir beautifulsoup==4.12.2 && \
    pip install --no-cache-dir googletrans==4.0.2

COPY . .


CMD ["python", "main.py"]
