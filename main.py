import telebot
import requests
import re
import html
import os
from Crypto.Cipher import AES
from flask import Flask
from threading import Thread

# ==========================================
# 1. إعدادات السيرفر الوهمي (لإبقاء البوت حياً)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "<b>I am alive!</b> Bot is running 24/7..."

def run():
    # تشغيل سيرفر ويب على المنفذ 8080
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ==========================================

# 2. إعدادات البوت
API_TOKEN = os.getenv('BOT_TOKEN')

if not API_TOKEN:
    print("❌ Error: No Token found.")
    # لا تضع التوكن هنا، تأكد أنه في Environment Variables
    exit(1)

bot = telebot.TeleBot(API_TOKEN)

def bypass_protection():
    """دالة لتجاوز حماية Cloudflare/Aes"""
    s = requests.Session()
    s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    try:
        r = s.get('https://asmodeus.free.nf/', timeout=15)
        nums = re.findall(r'toNumbers\("([a-f0-9]+)"\)', r.text)
        if len(nums) >= 3:
            key, iv, data = [bytes.fromhex(n) for n in nums[:3]]
            cookie_value = AES.new(key, AES.MODE_CBC, iv).decrypt(data).hex()
            s.cookies.set('__test', cookie_value, domain='asmodeus.free.nf')
            s.get('https://asmodeus.free.nf/index.php?i=1', timeout=15)
            return s
    except: return None
    return None

def clean_response(raw_text):
    if not raw_text: return ""
    text = html.unescape(raw_text)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<.*?>', '', text)
    return text.strip()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ أهلاً! البوت يعمل الآن 24/7 ولن يتوقف بإذن الله.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
    session = bypass_protection()
    if not session:
        bot.reply_to(message, "⚠️ الخادم مشغول أو محظور مؤقتاً.")
        return

    try:
        res = session.post('https://asmodeus.free.nf/deepseek.php', 
                          data={'model': 'DeepSeek-R1', 'question': message.text}, 
                          timeout=60)
        
        match = re.search(r'<div class="response-content">(.*?)</div>', res.text, re.DOTALL)
        if match:
            final_reply = clean_response(match.group(1))
            if final_reply:
                bot.reply_to(message, final_reply)
            else:
                bot.reply_to(message, "🤖 الرد كان فارغاً.")
        else:
            bot.reply_to(message, "⚠️ لم أتمكن من قراءة الرد.")
    except Exception as e:
        bot.reply_to(message, "🔌 حدث خطأ في الاتصال.")

# ==========================================
# 3. التشغيل
# ==========================================
if __name__ == "__main__":
    # تشغيل السيرفر الوهمي في الخلفية
    keep_alive()
    
    # تشغيل البوت
    print("🚀 Web server started. Bot is polling...")
    bot.infinity_polling()
