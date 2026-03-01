import subprocess
import os
import logging
import asyncio
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# إعداد السجلات
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

def get_control_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🛑 إيقاف البث", callback_data="stop"),
            InlineKeyboardButton("📊 الحالة", callback_data="status")
        ],
        [InlineKeyboardButton("🔄 تحديث القائمة", callback_data="start_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "✨ **مرحباً بك في بوت البث الاحترافي المحدث**\n\n"
        "🚀 **الأوامر المتاحة:**\n"
        "1️⃣ `/play [URL]` : لبث فيديو (يدعم يوتيوب/روابط مباشرة).\n"
        "2️⃣ `/radio [Audio_URL] [Image_URL]` : لبث صوت مع صورة.\n\n"
        "استخدم الأزرار أدناه للتحكم:"
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=get_control_keyboard(), parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=get_control_keyboard(), parse_mode="Markdown")

async def play_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ffmpeg_process
    if not context.args:
        await update.message.reply_text("⚠️ ارسل رابط الفيديو: `/play URL`", parse_mode="Markdown")
        return

    kill_process()
    url = context.args[0]
    msg = await update.message.reply_text("⏳ جاري استخراج رابط البث...")

    ydl_opts = {'format': 'best', 'quiet': True, 'noplaylist': True}
    
    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            stream_url = info['url']
        
        cmd = [
            "ffmpeg", "-re", 
            "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5",
            "-i", stream_url, 
            "-c", "copy", "-f", "flv", RTMP
        ]
        ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await msg.edit_text("✅ بدأ بث الفيديو بنجاح.", reply_markup=get_control_keyboard())
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {e}")

async def play_radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ffmpeg_process
    if not context.args:
        await update.message.reply_text("⚠️ ارسل رابط الصوت: `/radio URL_AUDIO [URL_IMG]`", parse_mode="Markdown")
        return

    kill_process()
    audio_url = context.args[0]
    image_url = context.args[1] if len(context.args) > 1 else None

    # إضافة \r\n ضروري لعمل headers في FFmpeg بشكل صحيح
    input_options = [
        "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5",
        "-headers", "User-Agent: Mozilla/5.0\r\n"
    ]

    if image_url:
        input_args = [*input_options, "-loop", "1", "-i", image_url, *input_options, "-i", audio_url]
        v_filter = "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p"
    else:
        input_args = ["-f", "lavfi", "-i", "color=c=black:s=1280x720:r=2", *input_options, "-i", audio_url]
        v_filter = "format=yuv420p"

    cmd = [
        "ffmpeg", "-re",
        *input_args,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
        "-vf", v_filter,
        "-c:a", "aac", "-ar", "44100", "-b:a", "128k", "-ac", "2",
        "-shortest", "-f", "flv", RTMP
    ]

    try:
        ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL)
        await update.message.reply_text("📻 بدأ بث الراديو (صوت + صورة).", reply_markup=get_control_keyboard())
    except Exception as e:
        await update.message.reply_text(f"❌ فشل البث: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "stop":
        kill_process()
        await query.edit_message_text("🛑 تم إيقاف البث.", reply_markup=get_control_keyboard())
    elif query.data == "status":
        status_text = "🟢 يعمل" if ffmpeg_process and ffmpeg_process.poll() is None else "🔴 متوقف"
        await query.edit_message_text(f"📊 الحالة: {status_text}", reply_markup=get_control_keyboard())
    elif query.data == "start_menu":
        await start(update, context)

if __name__ == "__main__":
    if not TOKEN or not RTMP:
        print("CRITICAL ERROR: BOT_TOKEN or RTMP_URL missing!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("play", play_video))
        app.add_handler(CommandHandler("radio", play_radio))
        app.add_handler(CallbackQueryHandler(button_handler))
        print("Bot is running...")
        app.run_polling()
