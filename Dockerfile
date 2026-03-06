FROM python:3.11-slim

WORKDIR /app

# تثبيت المكتبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn && \
    which gunicorn && gunicorn --version

# نسخ الكود
COPY bot.py .

# إنشاء مجلدات البيانات
RUN mkdir -p data/mem data/cfg data/tmp

EXPOSE 5000

# تشغيل بـ python -m gunicorn لضمان إيجاده
CMD ["python", "-m", "gunicorn", "bot:app", \
     "--workers", "2", \
     "--timeout", "120", \
     "--bind", "0.0.0.0:5000", \
     "--log-level", "info"]
