FROM python:3.11

RUN apt update && apt install -y ffmpeg

WORKDIR /app

COPY bot.py .

RUN pip install python-telegram-bot

CMD ["python", "bot.py"]