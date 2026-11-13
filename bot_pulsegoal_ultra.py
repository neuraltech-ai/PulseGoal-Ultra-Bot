import os, time, threading, requests
from flask import Flask, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
WEBAPP_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://pulsegoal-ultra-bot.onrender.com")
PORT = int(os.environ.get("PORT", 8080))

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True) if BOT_TOKEN else None

HTML_UI = """<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>PulseGoal Ultra</title><script src="https://cdn.tailwindcss.com"></script><script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script></head><body class="bg-slate-950 text-white p-4 font-sans"><div class="max-w-4xl mx-auto space-y-4"><div class="flex items-center justify-between bg-slate-900 p-4 rounded-2xl border border-slate-800"><h1 class="text-lg font-extrabold text-emerald-400">⚽ PulseGoal Ultra — البث الذكي بدون تقطيع</h1><span class="text-xs bg-emerald-500/20 text-emerald-300 px-3 py-1 rounded-full">Adaptive HLS + درع الإنترنت الضعيف</span></div><div class="aspect-video bg-black rounded-2xl overflow-hidden border border-slate-800"><video id="v" class="w-full h-full" controls playsinline></video></div><div class="flex flex-wrap gap-2 bg-slate-900 p-3 rounded-2xl border border-slate-800"><button onclick="setQ(-1)" class="px-3 py-1.5 bg-emerald-600 rounded-xl text-xs font-bold">⚡ تلقائي ذكي (ABR)</button><button onclick="setQ(0)" class="px-3 py-1.5 bg-amber-600 rounded-xl text-xs font-bold">🛡️ 240p (نت ضعيف جداً)</button><button onclick="setQ(1)" class="px-3 py-1.5 bg-slate-800 rounded-xl text-xs font-bold">480p SD مستقر</button><button onclick="setQ(2)" class="px-3 py-1.5 bg-slate-800 rounded-xl text-xs font-bold">1080p FHD</button></div></div><script>const v=document.getElementById('v'),s='https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8';let h=null;if(Hls.isSupported()){h=new Hls({maxBufferLength:30,lowLatencyMode:true});h.loadSource(s);h.attachMedia(v);}else if(v.canPlayType('application/vnd.apple.mpegurl')){v.src=s;}function setQ(l){if(h)h.currentLevel=l;}</script></body></html>"""

@app.route("/")
def index():
    return HTML_UI

@app.route("/health")
def health():
    return jsonify({"status": "online", "bot": "PulseGoal Ultra"}), 200

if bot:
    @bot.message_handler(commands=["start", "help"])
    def welcome(msg):
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(InlineKeyboardButton("📺 فتح مشغل البث الذكي (بدون تقطيع)", web_app=WebAppInfo(url=WEBAPP_URL)))
        kb.add(
            InlineKeyboardButton("🔴 مباريات الآن", url=WEBAPP_URL),
            InlineKeyboardButton("🛡️ طور الإنترنت الضعيف (240p)", url=WEBAPP_URL)
        )
        bot.send_message(msg.chat.id, "⚽ <b>مرحباً بك في PulseGoal Ultra</b>\nمشاهدة المباريات العالمية بجودة تكيفية بدون تقطيع حتى مع الإنترنت الضعيف:", reply_markup=kb)

def poll():
    while bot:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=poll, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)
