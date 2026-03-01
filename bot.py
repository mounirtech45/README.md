import subprocess
import os
import logging
import asyncio
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
RTMP = os.getenv("RTMP_URL")

ffmpeg_process = None

def kill_process():
    global ffmpeg_process
    if ffmpeg_process:
        try:
            ffmpeg_process.kill()
            ffmpeg_process.wait(timeout=2)
        except: pass
        ffmpeg_process = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **بوت البث المباشر المباشر**\n\n"
        "📺 لبث فيديو: `/play URL`\n"
        "📻 لبث راديو (MP3): `/radio رابط_الصوت رابط_الصورة`",
        parse_mode="Markdown"
    )

async def play_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ffmpeg_process
    if not context.args:
        return await update.message.reply_text("⚠️ أرسل الرابط بعد الأمر.")
    
    kill_process()
    url = context.args[0]
    msg = await update.message.reply_text("⏳ جاري بدء بث الفيديو...")

    try:
        ydl_opts = {'format': 'best', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, download=False)
            stream_url = info['url']
        
        # بث الفيديو مباشرة بدون إعادة ترميز ثقيلة
        cmd = ["ffmpeg", "-re", "-i", stream_url, "-c", "copy", "-f", "flv", RTMP]
        ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        await msg.edit_text("✅ بدأ بث الفيديو.")
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {e}")

async def play_radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ffmpeg_process
    if not context.args:
        return await update.message.reply_text("⚠️ أرسل رابط MP3.")

    kill_process()
    audio_url = context.args[0]
    # صورة افتراضية في حال لم يرسل المستخدم رابط صورة
    image_url = context.args[1] if len(context.args) > 1 else "https://via.placeholder.com/1280x720.png?text=LIVE+RADIO"
    
    msg = await update.message.reply_text("⏳ جاري تشغيل الـ MP3...")

    # أهم إعدادات لضمان عمل الصوت MP3 مع الصورة في البث المباشر
    cmd = [
        "ffmpeg", "-re",
        "-loop", "1", "-i", image_url,              # المدخل 0: الصورة
        "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5",
        "-i", audio_url,                             # المدخل 1: الصوت
        "-map", "0:v:0",                             # خذ الفيديو من الصورة
        "-map", "1:a:0",                             # خذ الصوت من رابط الـ MP3
        "-c:v", "libx264", "-preset", "ultrafast",   # ترميز الفيديو (خفيف جداً)
        "-tune", "stillimage",
        "-vf", "scale=1280:720,format=yuv420p",      # توحيد المقاس
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", # تحويل الصوت لـ AAC المتوافق مع البث
        "-shortest",                                 # التوقف عند انتهاء الصوت
        "-f", "flv", RTMP
    ]

    try:
        ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        await msg.edit_text("✅ الراديو يعمل الآن بنجاح.")
    except Exception as e:
        await msg.edit_text(f"❌ فشل تشغيل الصوت: {e}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kill_process()
    await update.message.reply_text("🛑 تم إيقاف البث.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play_video))
    app.add_handler(CommandHandler("radio", play_radio))
    app.add_handler(CommandHandler("stop", stop))
    print("Bot is started...")
    app.run_polling()
