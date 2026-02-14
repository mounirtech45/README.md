import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8018362390:AAFB3YxP6ZGVSI5tdxLHLjoa54UygNGwG2s"
RTMP = "rtmps://dc4-1.rtmp.t.me/s/2474957244:XCMZwzGZIZ1d6K_JXFGkFg"

ffmpeg_process = None

# تشغيل بث
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

# ايقاف بث
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global ffmpeg_process

    if ffmpeg_process:
        ffmpeg_process.kill()
        ffmpeg_process = None
        await update.message.reply_text("تم ايقاف البث")
    else:
        await update.message.reply_text("لا يوجد بث")

# حالة
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if ffmpeg_process:
        await update.message.reply_text("البث يعمل")
    else:
        await update.message.reply_text("البث متوقف")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("play", play))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(CommandHandler("status", status))

print("Bot Running")

app.run_polling()