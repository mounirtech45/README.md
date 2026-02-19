import subprocess
import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# إعداد السجلات لمراقبة الأداء والأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("BOT_TOKEN")
RTMP = os.getenv("RTMP_URL")

ffmpeg_process = None

def kill_process():
    global ffmpeg_process
    if ffmpeg_process:
        try:
            ffmpeg_process.kill()
            ffmpeg_process.wait(timeout=5)
        except Exception:
            pass
        ffmpeg_process = None
        logging.info("Stream process terminated.")

# 1. بث فيديو مباشر (نسخ أصلي بدون معالجة لتوفير المعالج)
async def play_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ffmpeg_process
    if not context.args:
        await update.message.reply_text("⚠️ أرسل الرابط: /play <URL>")
        return

    url = context.args[0]
    kill_process()

    cmd = [
        "ffmpeg", "-re", "-i", url,
        "-c", "copy", "-f", "flv", RTMP
    ]

    try:
        ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await update.message.reply_text("✅ بدأ بث الفيديو بنجاح.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

# 2. بث صوت مع صورة (راديو) - إعدادات متوافقة جداً
async def play_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ffmpeg_process
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ أرسل الروابط: /radio <صوت> <صورة>")
        return

    audio_url = context.args[0]
    image_url = context.args[1]
    kill_process()

    # إعدادات تضمن عمل الصوت على يوتيوب وفيس بوك بأقل موارد
    cmd = [
        "ffmpeg",
        "-re",
        "-loop", "1",
        "-i", image_url,
        "-i", audio_url,
        # معالجة الصورة: تحجيم قياسي وتنسيق بكسل متوافق
        "-vf", "scale=1280:720,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "stillimage",
        "-r", "2", # فريمات منخفضة جداً لتوفير المعالج
        # معالجة الصوت: ترميز AAC مع تردد قياسي 44100
        "-c:a", "aac",
        "-ar", "44100",
        "-b:a", "128k",
        "-shortest",
        "-f", "flv",
        RTMP
    ]

    try:
        ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await update.message.reply_text("📻 بدأ بث الراديو (صوت + صورة).")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ في بدء الراديو: {e}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kill_process()
    await update.message.reply_text("🛑 تم إيقاف جميع العمليات.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ffmpeg_process and ffmpeg_process.poll() is None:
        await update.message.reply_text("🟢 البث نشط حالياً.")
    else:
        await update.message.reply_text("🔴 لا يوجد بث نشط.")

if __name__ == "__main__":
    if not TOKEN or not RTMP:
        print("Missing BOT_TOKEN or RTMP_URL!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("play", play_video))
        app.add_handler(CommandHandler("radio", play_audio))
        app.add_handler(CommandHandler("stop", stop))
        app.add_handler(CommandHandler("status", status))
        print("Bot is alive...")
        app.run_polling()
