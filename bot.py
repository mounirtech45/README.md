import subprocess
import os
import logging
import asyncio
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
RTMP = os.getenv("RTMP_URL")

ffmpeg_process = None
user_data_store = {}

def kill_process():
    global ffmpeg_process
    if ffmpeg_process:
        try:
            ffmpeg_process.terminate() # استخدام terminate أولاً لضمان الإغلاق النظيف
            ffmpeg_process.wait(timeout=5)
        except Exception:
            try: ffmpeg_process.kill()
            except: pass
        ffmpeg_process = None

def get_quality_keyboard(mode):
    keyboard = [
        [
            InlineKeyboardButton("360p", callback_data=f"q_360_{mode}"),
            InlineKeyboardButton("720p", callback_data=f"q_720_{mode}"),
            InlineKeyboardButton("1080p", callback_data=f"q_1080_{mode}")
        ],
        [InlineKeyboardButton("🛑 إيقاف التشغيل", callback_data="stop")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "✨ **بوت البث المباشر المطور**\n\nأرسل رابط فيديو أو صوت باستخدام الأوامر:\n1️⃣ `/play URL` لبث فيديو\n2️⃣ `/radio Audio_URL Image_URL` لبث صوت مع صورة"
    await update.message.reply_text(text, parse_mode="Markdown")

async def play_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("⚠️ ارسل الرابط: `/play URL`")
    user_id = update.effective_user.id
    user_data_store[user_id] = {'url': context.args[0]}
    await update.message.reply_text("🎬 اختر جودة الفيديو:", reply_markup=get_quality_keyboard("video"))

async def play_radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("⚠️ ارسل رابط الصوت: `/radio URL_AUDIO [URL_IMG]`")
    user_id = update.effective_user.id
    user_data_store[user_id] = {
        'audio': context.args[0],
        'image': context.args[1] if len(context.args) > 1 else "https://via.placeholder.com/1280x720.png?text=Live+Radio"
    }
    await update.message.reply_text("📻 اختر جودة البث (الراديو):", reply_markup=get_quality_keyboard("radio"))

async def handle_quality_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ffmpeg_process
    query = update.callback_query
    data = query.data.split("_")
    res = data[1]
    mode = data[2]
    user_id = query.from_user.id

    if user_id not in user_data_store:
        return await query.edit_message_text("❌ خطأ: انتهت الجلسة. أعد إرسال الرابط.")

    kill_process()
    await query.edit_message_text(f"⏳ جاري بدء البث بدقة {res}p...")

    # إعدادات العرض
    width = int(res)
    height = (width * 9) // 16
    v_bitrate = "1000k" if res == "360" else "2500k" if res == "720" else "4500k"

    try:
        if mode == "video":
            url = user_data_store[user_id]['url']
            ydl_opts = {'format': f'bestvideo[height<={res}]+bestaudio/best/best', 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                stream_url = info['url']
            
            cmd = [
                "ffmpeg", "-re", "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5",
                "-i", stream_url, "-c:v", "libx264", "-preset", "veryfast", "-b:v", v_bitrate,
                "-maxrate", v_bitrate, "-bufsize", "2000k", "-vf", f"scale={width}:{height},format=yuv420p",
                "-c:a", "aac", "-b:a", "128k", "-f", "flv", RTMP
            ]
        
        else: # وضع الراديو المصلح لروابط MP3
            audio_url = user_data_store[user_id]['audio']
            image_url = user_data_store[user_id]['image']
            
            cmd = [
                "ffmpeg", "-re",
                "-loop", "1", "-i", image_url, # المدخل 0: الصورة
                "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5",
                "-i", audio_url, # المدخل 1: ملف MP3
                "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
                "-b:v", v_bitrate, "-vf", f"scale={width}:{height},format=yuv420p",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
                "-map", "0:v:0", "-map", "1:a:0", # توجيه الصورة للصورة والصوت للصوت
                "-shortest", "-f", "flv", RTMP
            ]

        ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        await query.edit_message_text(f"✅ البث يعمل الآن ({res}p)\n📻 الرابط: {user_data_store[user_id].get('audio', 'Video')}")
    
    except Exception as e:
        await query.edit_message_text(f"❌ فشل البث: {str(e)}")

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("q_"):
        await handle_quality_selection(update, context)
    elif query.data == "stop":
        kill_process()
        await query.edit_message_text("🛑 تم إيقاف البث بنجاح.")
    elif query.data == "status":
        status = "🟢 يعمل حالياً" if ffmpeg_process and ffmpeg_process.poll() is None else "🔴 متوقف"
        await query.edit_message_text(f"📊 الحالة الحالية: {status}")

if __name__ == "__main__":
    if not TOKEN or not RTMP:
        print("ERROR: BOT_TOKEN or RTMP_URL missing!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("play", play_video))
        app.add_handler(CommandHandler("radio", play_radio))
        app.add_handler(CallbackQueryHandler(callback_router))
        print("Bot is LIVE...")
        app.run_polling()
