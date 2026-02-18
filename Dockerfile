FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY bot.py .

# تثبيت المكتبة مباشرة بدون الحاجة لملف requirements.txt
RUN pip install --no-cache-dir python-telegram-bot==20.*

CMD ["python", "bot.py"]
