# استخدام نسخة بايثون خفيفة
FROM python:3.11-slim

# تحديث النظام وتثبيت FFmpeg والأدوات الضرورية
RUN apt-get update && \
    apt-get install -y ffmpeg curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# تحديد مجلد العمل
WORKDIR /app

# نسخ ملف المكتبات أولاً لاستغلال خاصية الكاش في دوكر
COPY requirements.txt .

# تثبيت مكتبات بايثون
RUN pip install --no-cache-dir -r requirements.txt

# نسخ ملف البوت
COPY bot.py .

# تشغيل البوت
CMD ["python", "bot.py"]
