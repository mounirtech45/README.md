import subprocess
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# جلب القيم من إعدادات البيئة في ريلوي
TOKEN = os.getenv("BOT_TOKEN")
RTMP = os.getenv("RTMP_URL")

ffmpeg_process = None

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ffmpeg_process
    if len(context.args) == 0:
        await update.message.reply_text("ارسل رابط m3u8")
        return

    url = context.args[0]
    if ffmpeg_process:
        ffmpeg_process.kill()

    cmd = [
        "ffmpeg",
        "-re",
        "-i", url,
        "-c", "copy",
        "-f", "flv",
        RTMP
    ]

    ffmpeg_process = subprocess.Popen(cmd)
    await update.message.reply_text("تم بدء البث")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ffmpeg_process
    if ffmpeg_process:
        ffmpeg_process.kill()
        ffmpeg_process = None
        await update.message.reply_text("تم ايقاف البث")
    else:
        await update.message.reply_text("لا يوجد بث")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ffmpeg_process:
        await update.message.reply_text("البث يعمل")
    else:
        await update.message.reply_text("البث متوقف")

if __name__ == "__main__":
    if not TOKEN or not RTMP:
        print("Error: BOT_TOKEN or RTMP_URL not found in environment variables!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("play", play))
        app.add_handler(CommandHandler("stop", stop))
        app.add_handler(CommandHandler("status", status))
        print("Bot Running...")
        app.run_polling()
