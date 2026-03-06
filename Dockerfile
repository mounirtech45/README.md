FROM python:3.11-slim

# مجلد العمل
WORKDIR /app

# تثبيت المكتبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY bot.py .

# إنشاء مجلدات البيانات
RUN mkdir -p data/mem data/cfg data/tmp

# المنفذ
EXPOSE 5000

# تشغيل gunicorn
CMD ["gunicorn", "bot:app", \
     "--workers", "2", \
     "--timeout", "120", \
     "--bind", "0.0.0.0:5000", \
     "--log-level", "info"]
