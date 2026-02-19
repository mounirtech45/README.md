import subprocess
import os
import logging
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
        "✨ **مرحباً بك في بوت البث الاحترافي**\n\n"
        "🚀 **الأوامر المتاحة:**\n"
        "1️⃣ `/play [URL]` : لبث فيديو مباشر (m3u8/mp4).\n"
        "2️⃣ `/radio [Audio_URL] [Image_URL]` : لبث صوت مع صورة (الصورة اختيارية).\n\n"
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
    
    # وضع النسخ المباشر للفيديو لتوفير موارد المعالج
    cmd = [
        "ffmpeg", "-re", 
        "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5",
        "-i", url, 
        "-c", "copy", "-f", "flv", RTMP
    ]
    
    try:
        ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await update.message.reply_text("✅ بدأ بث الفيديو بنجاح.", reply_markup=get_control_keyboard())
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

async def play_radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ffmpeg_process
    if not context.args:
        await update.message.reply_text("⚠️ ارسل رابط الصوت: `/radio URL_AUDIO [URL_IMG]`", parse_mode="Markdown")
        return

    kill_process()
    audio_url = context.args[0]
    image_url = context.args[1] if len(context.args) > 1 else None

    # إعدادات متقدمة لضمان سحب ملفات MP3 بنجاح وتجاوز حماية السيرفرات
    input_options = [
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",
        "-headers", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ]

    if image_url:
        input_args = [*input_options, "-loop", "1", "-i", image_url, *input_options, "-i", audio_url]
        v_filter = "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p"
    else:
        # خلفية سوداء في حال عدم وجود صورة
        input_args = ["-f", "lavfi", "-i", "color=c=black:s=1280x720:r=2", *input_options, "-i", audio_url]
        v_filter = "format=yuv420p"

    cmd = [
        "ffmpeg", "-re",
        *input_args,
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
        "-vf", v_filter,
        "-c:a", "aac", "-ar", "44100", "-b:a", "128k", "-ac", "2",
        "-r", "2", "-g", "4", "-f", "flv", RTMP
    ]

    try:
        ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await update.message.reply_text("📻 بدأ معالجة الصوت وبثه (راديو).", reply_markup=get_control_keyboard())
    except Exception as e:
        await update.message.reply_text(f"❌ فشل البث: {e}")

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
