FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y ffmpeg curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

ENV BOT_TOKEN=""
ENV RTMP_URL=""

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import telegram; print('OK')" || exit 1

CMD ["python", "-u", "bot.py"]
