import os
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from yt_dlp import YoutubeDL

# إعداد السجلات لمتابعة العمليات في Railway Logs
logging.basicConfig(level=logging.INFO)

# جلب المتغيرات من إعدادات Railway
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT = int(os.getenv("CHAT_ID")) # آيدي القناة/المجموعة (يبدأ بـ -100)

# إعداد العميل
app = Client("streaming_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
call_py = PyTgCalls(app)

# دالة استخراج رابط البث المباشر
def get_stream_url(url):
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'noplaylist': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info['url']

@app.on_message(filters.command("start") & filters.private)
async def start(client, message: Message):
    text = (
        "🚀 **مرحباً بك في بوت بث القنوات**\n\n"
        f"سيتم البث في القناة: `{TARGET_CHAT}`\n\n"
        "**الأوامر:**\n"
        "1️⃣ `/play [الرابط]` : لبدء البث.\n"
        "2️⃣ `/stop` : لإيقاف البث.\n"
    )
    await message.reply_text(text, parse_mode="Markdown")

@app.on_message(filters.command("play"))
async def play_video(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("⚠️ يرجى إرسال الرابط: `/play URL`")
    
    url = message.command[1]
    msg = await message.reply_text("⏳ جاري استخراج الرابط والاتصال بالمكالمة...")
    
    try:
        stream_url = get_stream_url(url)
        
        # الانضمام والبث في القناة المحددة في المتغيرات
        await call_py.play(
            TARGET_CHAT,
            MediaStream(stream_url)
        )
        await msg.edit_text(f"✅ بدأ البث بنجاح في القناة:\n`{TARGET_CHAT}`")
    except Exception as e:
        await msg.edit_text(f"❌ فشل البث: {str(e)}")

@app.on_message(filters.command("stop"))
async def stop_stream(client, message: Message):
    try:
        await call_py.leave_call(TARGET_CHAT)
        await message.reply_text("🛑 تم إيقاف البث بنجاح.")
    except:
        await message.reply_text("⚠️ لا يوجد بث نشط حالياً.")

async def main():
    await app.start()
    await call_py.start()
    logging.info("Bot & PyTgCalls Started!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
