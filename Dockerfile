FROM python:3.11-slim

# تثبيت FFmpeg وgit (إن لزم) وتنظيف ملفات الكاش لتقليل الحجم
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# نسخ الملفات
COPY requirements.txt .
COPY bot.py .

# تثبيت المكتبات
RUN pip install --no-cache-dir -r requirements.txt

# تشغيل البوت
CMD ["python", "bot.py"]
