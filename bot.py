import subprocess
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# إعداد السجلات
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
RTMP = os.getenv("RTMP_URL")

# متغير عالمي لتخزين العملية
ffmpeg_process = None

def kill_process():
    global ffmpeg_process
    if ffmpeg_process:
        ffmpeg_process.kill()
        ffmpeg_process = None

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
        "1️⃣ `/play [link]` : لبث فيديو مباشر (m3u8/mp4).\n"
        "2️⃣ `/radio [audio_link] [image_link]` : لبث صوت مع صورة (الصورة اختيارية).\n\n"
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
    
    # أمر الفيديو (Copy mode) لتوفير الموارد
    cmd = ["ffmpeg", "-re", "-i", url, "-c", "copy", "-f", "flv", RTMP]
    
    ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    await update.message.reply_text("✅ تم بدء بث الفيديو..", reply_markup=get_control_keyboard())

async def play_radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ffmpeg_process
    if not context.args:
        await update.message.reply_text("⚠️ ارسل رابط الصوت: `/radio URL_AUDIO [URL_IMG]`", parse_mode="Markdown")
        return

    kill_process()
    audio_url = context.args[0]
    image_url = context.args[1] if len(context.args) > 1 else None

    # بناء الأمر ديناميكياً (إذا لم توجد صورة يستخدم خلفية سوداء)
    if image_url:
        input_args = ["-loop", "1", "-i", image_url, "-i", audio_url]
        v_filter = "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p"
    else:
        # خلفية سوداء في حال عدم وجود صورة
        input_args = ["-f", "lavfi", "-i", "color=c=black:s=1280x720:r=2", "-i", audio_url]
        v_filter = "format=yuv420p"

    cmd = [
        "ffmpeg", "-re",
        *input_args,
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
        "-vf", v_filter,
        "-c:a", "aac", "-ar", "44100", "-b:a", "128k",
        "-r", "2", "-g", "4", "-f", "flv", RTMP
    ]

    try:
        ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await update.message.reply_text("📻 بدأ بث الراديو الآن..", reply_markup=get_control_keyboard())
    except Exception as e:
        await update.message.reply_text(f"❌ فشل البث: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "stop":
        kill_process()
        await query.edit_message_text("🛑 تم إيقاف البث بنجاح.", reply_markup=get_control_keyboard())
    
    elif query.data == "status":
        status = "🟢 يعمل" if ffmpeg_process and ffmpeg_process.poll() is None else "🔴 متوقف"
        await query.edit_message_text(f"📊 حالة البث الحالية: {status}", reply_markup=get_control_keyboard())
    
    elif query.data == "start_menu":
        await start(update, context)

if __name__ == "__main__":
    if not TOKEN or not RTMP:
        print("Set BOT_TOKEN and RTMP_URL first!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("play", play_video))
        app.add_handler(CommandHandler("radio", play_radio))
        app.add_handler(CallbackQueryHandler(button_handler))
        
        print("Professional Bot Running...")
        app.run_polling()
