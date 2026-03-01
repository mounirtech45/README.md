# 🎙️ بوت البث المباشر على تيليغرام

بوت تيليغرام يتيح بث الفيديو والراديو مباشرة إلى أي خادم RTMP (مثل YouTube Live, Facebook Live).

---

## ⚙️ المتطلبات

- Docker
- توكن بوت تيليغرام (من [@BotFather](https://t.me/BotFather))
- رابط RTMP الخاص بك

---

## 🚀 طريقة التشغيل

### باستخدام Docker:

```bash
docker build -t stream-bot .

docker run -d \
  -e BOT_TOKEN="توكن_البوت" \
  -e RTMP_URL="rtmp://a.rtmp.youtube.com/live2/STREAM_KEY" \
  --name stream-bot \
  stream-bot
```

### بدون Docker:

```bash
pip install -r requirements.txt
export BOT_TOKEN="توكن_البوت"
export RTMP_URL="rtmp://..."
python bot.py
```

---

## 📋 الأوامر

| الأمر | الوصف |
|-------|-------|
| `/start` | عرض القائمة الرئيسية |
| `/play [URL]` | بث فيديو مباشر (m3u8 / mp4) |
| `/radio [Audio_URL] [Image_URL]` | بث صوت مع صورة (الصورة اختيارية) |

---

## 🎛️ أزرار التحكم

- 🛑 **إيقاف البث** — يوقف FFmpeg فوراً
- 📊 **الحالة** — يعرض هل البث يعمل أم لا
- 🔄 **تحديث القائمة** — يعيد عرض القائمة الرئيسية

---

## 📝 ملاحظات

- يدعم روابط m3u8 و mp4 و mp3
- عند استخدام `/radio` بدون صورة، تظهر خلفية سوداء تلقائياً
- يجب أن يكون FFmpeg مثبتاً على الجهاز عند التشغيل بدون Docker
