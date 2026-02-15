import telebot
import requests
import re
import html
import os
from Crypto.Cipher import AES

# جلب التوكن من متغيرات البيئة (إعدادات الاستضافة)
# لا تقم بوضع التوكن هنا مباشرة للحفاظ على أمان حسابك
API_TOKEN = os.getenv('BOT_TOKEN')

# التحقق من وجود التوكن
if not API_TOKEN:
    print("❌ خطأ: لم يتم العثور على التوكن. تأكد من إضافته في Environment Variables في Render.")
    # يمكن وضع توكن مؤقت للاختبار المحلي فقط، ولكن احذفه قبل الرفع
    # API_TOKEN = "ضع_توكن_للاختبار_المحلي_فقط" 

if API_TOKEN:
    bot = telebot.TeleBot(API_TOKEN)
else:
    exit(1)

def bypass_protection():
    """دالة لتجاوز حماية الموقع المستهدف"""
    s = requests.Session()
    s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    try:
        # محاولة الاتصال الأولي
        r = s.get('https://asmodeus.free.nf/', timeout=15)
        
        # استخراج مفاتيح التشفير
        nums = re.findall(r'toNumbers\("([a-f0-9]+)"\)', r.text)
        if len(nums) >= 3:
            key, iv, data = [bytes.fromhex(n) for n in nums[:3]]
            cookie_value = AES.new(key, AES.MODE_CBC, iv).decrypt(data).hex()
            
            # تعيين الكوكيز
            s.cookies.set('__test', cookie_value, domain='asmodeus.free.nf')
            
            # إعادة توجيه للتحقق
            s.get('https://asmodeus.free.nf/index.php?i=1', timeout=15)
            return s
    except Exception as e:
        print(f"Error in bypass: {e}")
        return None
    return None

def clean_response(raw_text):
    """تنظيف النص من التفكير وأكواد HTML"""
    if not raw_text: return ""
    text = html.unescape(raw_text)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<.*?>', '', text)
    return text.strip()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ أهلاً بك! البوت يعمل الآن على الاستضافة السحابية.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # إرسال حالة 'يكتب...' للمستخدم
    bot.send_chat_action(message.chat.id, 'typing')
    
    session = bypass_protection()
    if not session:
        bot.reply_to(message, "⚠️ عذراً، لم أتمكن من الاتصال بالخادم (قد يكون محظوراً من الاستضافة).")
        return

    try:
        # إرسال السؤال
        res = session.post('https://asmodeus.free.nf/deepseek.php', 
                          data={'model': 'DeepSeek-R1', 'question': message.text}, 
                          timeout=60)
        
        # استخراج الإجابة
        match = re.search(r'<div class="response-content">(.*?)</div>', res.text, re.DOTALL)
        if match:
            final_reply = clean_response(match.group(1))
            if final_reply:
                bot.reply_to(message, final_reply)
            else:
                bot.reply_to(message, "🤖 الرد كان فارغاً.")
        else:
            bot.reply_to(message, "⚠️ لم أتمكن من قراءة الرد من المصدر.")
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "🔌 حدث خطأ أثناء المعالجة.")

print("🚀 البوت يعمل الآن...")
bot.infinity_polling()
