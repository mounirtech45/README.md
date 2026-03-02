import subprocess
import os
import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# إعداد السجلات (Logs)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("BOT_TOKEN")
RTMP = os.getenv("RTMP_URL")

ffmpeg_process = None

# ───── روابط يوتيوب ─────
def is_youtube_url(url: str) -> bool:
    return bool(re.search(r'(youtube\.com|youtu\.be)', url))

def get_youtube_stream_url(url: str) -> str | None:
    """استخرج الرابط المباشر من يوتيوب باستخدام yt-dlp"""
    try:
        result = subprocess.run(
            ["yt-dlp", "-g", "--best-video", url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            stream_url = result.stdout.strip().split("\n")[0]
            return stream_url
        logging.error(f"yt-dlp error: {result.stderr}")
        return None
    except Exception as e:
        logging.error(f"yt-dlp exception: {e}")
        return None

# ───── إيقاف البث ─────
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

# ───── لوحة التحكم ─────
def get_control_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🛑 إيقاف البث", callback_data="stop"),
            InlineKeyboardButton("📊 الحالة", callback_data="status")
        ],
        [InlineKeyboardButton("🔄 تحديث القائمة", callback_data="start_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ───── أمر /start ─────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "✨ **مرحباً بك في بوت البث الاحترافي**\n\n"
        "🚀 **الأوامر المتاحة:**\n"
        "1️⃣ `/play [URL]` : بث فيديو مباشر (m3u8 / mp4 / يوتيوب).\n"
        "2️⃣ `/radio [Audio_URL] [Image_URL]` : بث صوت مع صورة (الصورة اختيارية).\n\n"
        "استخدم الأزرار أدناه للتحكم:"
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=get_control_keyboard(), parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=get_control_keyboard(), parse_mode="Markdown")

# ───── أمر /play ─────
async def play_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ffmpeg_process
    if not context.args:
        await update.message.reply_text("⚠️ ارسل رابط الفيديو: `/play URL`", parse_mode="Markdown")
        return

    kill_process()
    url = context.args[0]

    # ── يوتيوب: نستخرج الرابط المباشر أولاً ──
    if is_youtube_url(url):
        await update.message.reply_text("🔄 جاري استخراج رابط يوتيوب...")
        url = get_youtube_stream_url(url)
        if not url:
            await update.message.reply_text("❌ فشل استخراج رابط يوتيوب. تأكد أن الرابط صحيح وأن البث حي.")
            return

    # ── بث مباشر بالنسخ لتوفير موارد المعالج ──
    cmd = [
        "ffmpeg", "-re",
        "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5",
        "-i", url,
        "-c", "copy",
        "-f", "flv", RTMP
    ]

    try:
        ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await update.message.reply_text("✅ بدأ بث الفيديو بنجاح.", reply_markup=get_control_keyboard())
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

# ───── أمر /radio ─────
async def play_radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ffmpeg_process
    if not context.args:
        await update.message.reply_text("⚠️ ارسل رابط الصوت: `/radio URL_AUDIO [URL_IMG]`", parse_mode="Markdown")
        return

    kill_process()
    audio_url = context.args[0]
    image_url = context.args[1] if len(context.args) > 1 else None

    if image_url:
        cmd = [
            "ffmpeg", "-re",
            "-loop", "1",
            "-i", image_url,
            "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5",
            "-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "-i", audio_url,
            "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
            "-c:a", "aac", "-ar", "44100", "-b:a", "128k", "-ac", "2",
            "-r", "2", "-g", "4",
            "-shortest",
            "-f", "flv", RTMP
        ]
    else:
        cmd = [
            "ffmpeg", "-re",
            "-f", "lavfi", "-i", "color=c=black:s=1280x720:r=2",
            "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5",
            "-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "-i", audio_url,
            "-c:v", "libx264", "-preset", "ultrafast",
            "-vf", "format=yuv420p",
            "-c:a", "aac", "-ar", "44100", "-b:a", "128k", "-ac", "2",
            "-r", "2", "-g", "4",
            "-f", "flv", RTMP
        ]

    try:
        ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await update.message.reply_text("📻 بدأ بث الراديو بنجاح.", reply_markup=get_control_keyboard())
    except Exception as e:
        await update.message.reply_text(f"❌ فشل البث: {e}")

# ───── أزرار التحكم ─────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "stop":
        kill_process()
        await query.edit_message_text("🛑 تم إيقاف البث تماماً.", reply_markup=get_control_keyboard())

    elif query.data == "status":
        status_text = "🟢 البث يعمل حالياً" if ffmpeg_process and ffmpeg_process.poll() is None else "🔴 البث متوقف"
        await query.edit_message_text(f"📊 الحالة: {status_text}", reply_markup=get_control_keyboard())

    elif query.data == "start_menu":
        await start(update, context)

# ───── تشغيل البوت ─────
if __name__ == "__main__":
    if not TOKEN or not RTMP:
        print("CRITICAL ERROR: BOT_TOKEN or RTMP_URL missing in environment variables!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("play", play_video))
        app.add_handler(CommandHandler("radio", play_radio))
        app.add_handler(CallbackQueryHandler(button_handler))

        print("Bot is running perfectly...")
        app.run_polling()
