import subprocess
import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("BOT_TOKEN")
RTMP = os.getenv("RTMP_URL")

ffmpeg_process = None

# دالة لإيقاف العملية الحالية
def kill_process():
    global ffmpeg_process
    if ffmpeg_process:
        ffmpeg_process.kill()
        ffmpeg_process = None
        logging.info("Previous stream killed.")

# 1. بث فيديو (فيديو جاهز)
# يستهلك موارد قليلة جداً لأنه ينسخ الفيديو كما هو (Copy)
async def play_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ffmpeg_process
    
    if not context.args:
        await update.message.reply_text("⚠️ الاستخدام: /play <رابط_الفيديو>")
        return

    url = context.args[0]
    kill_process()

    cmd = [
        "ffmpeg",
        "-re",
        "-i", url,
        "-c", "copy",  # نسخ مباشر بدون تحويل لتقليل الضغط
        "-f", "flv",
        RTMP
    ]

    try:
        ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await update.message.reply_text(f"✅ تم بدء بث الفيديو.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

# 2. بث صوت مع صورة (راديو)
# تم تحسين الإعدادات لأقل استهلاك (2 فريم/ثانية فقط)
async def play_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ffmpeg_process

    if len(context.args) < 2:
        await update.message.reply_text("⚠️ الاستخدام: /radio <رابط_الصوت> <رابط_الصورة>")
        return

    audio_url = context.args[0]
    image_url = context.args[1]
    kill_process()

    cmd = [
        "ffmpeg",
        "-re",
        "-loop", "1",           # تكرار الصورة
        "-i", image_url,        # مدخل الصورة
        "-i", audio_url,        # مدخل الصوت
        "-c:v", "libx264",      # كودك الفيديو
        "-preset", "ultrafast", # أسرع وضع لتقليل استهلاك المعالج
        "-tune", "stillimage",  # تحسين للصورة الثابتة
        "-r", "2",              # 2 فريم في الثانية فقط (توفير هائل للموارد)
        "-c:a", "aac",          # كودك الصوت
        "-b:a", "128k",         # جودة صوت مناسبة
        "-shortest",            # إنهاء البث عند انتهاء الصوت
        "-f", "flv",
        RTMP
    ]

    try:
        ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await update.message.reply_text(f"✅ تم بدء بث الراديو (صوت+صورة).")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kill_process()
    await update.message.reply_text("🛑 تم إيقاف البث")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ffmpeg_process and ffmpeg_process.poll() is None:
        await update.message.reply_text("🟢 البث يعمل حالياً")
    else:
        await update.message.reply_text("🔴 البث متوقف")

if __name__ == "__main__":
    if not TOKEN or not RTMP:
        print("Error: BOT_TOKEN or RTMP_URL not found!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("play", play_video))   # للفيديو
        app.add_handler(CommandHandler("radio", play_audio))  # للصوت + صورة
        app.add_handler(CommandHandler("stop", stop))
        app.add_handler(CommandHandler("status", status))
        
        print("Bot Running...")
        app.run_polling()
