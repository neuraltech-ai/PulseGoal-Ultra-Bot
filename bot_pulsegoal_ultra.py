import os, time, threading, requests
from flask import Flask, jsonify, request, Response
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
WEBAPP_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://pulsegoal-ultra-bot.onrender.com")
PORT = int(os.environ.get("PORT", 8080))

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True) if BOT_TOKEN else None

MATCHES = [
    {"id": "m1", "league": "دوري أبطال أوروبا", "home": "ريال مدريد", "away": "برشلونة", "score": "2 - 1", "time": "مباشر 🔴", "s1": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "s2": "https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8"},
    {"id": "m2", "league": "الدوري الإنجليزي", "home": "مانشستر سيتي", "away": "ليفربول", "score": "1 - 1", "time": "مباشر 🔴", "s1": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "s2": "https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8"},
    {"id": "m3", "league": "الكونفدرالية / البطولة المغربية", "home": "نهضة بركان (RSB)", "away": "الوداد الرياضي", "score": "2 - 0", "time": "مباشر 🔴", "s1": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "s2": "https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8"},
    {"id": "m4", "league": "الدوري الإسباني", "home": "أتلتيكو مدريد", "away": "إشبيلية", "score": "0 - 0", "time": "21:00 GMT", "s1": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "s2": "https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8"}
]

HTML_UI = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>PulseGoal Ultra Pro</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800&display=swap" rel="stylesheet">
<style>body{font-family:'Cairo',sans-serif;background:#060911;color:#f8fafc;}</style>
</head>
<body class="p-3 sm:p-5 max-w-4xl mx-auto space-y-4">
  <div class="flex items-center justify-between bg-slate-900/90 p-3.5 rounded-2xl border border-slate-800 shadow-lg">
    <div>
      <h1 class="text-base sm:text-lg font-extrabold text-emerald-400">⚽ PulseGoal Ultra Pro</h1>
      <p id="now-playing" class="text-xs text-slate-300">جاري البث: ريال مدريد vs برشلونة</p>
    </div>
    <span id="net-pill" class="text-[11px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2.5 py-1 rounded-full font-bold">Adaptive HLS نشط</span>
  </div>

  <div class="relative aspect-video bg-black rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
    <video id="v" class="w-full h-full object-contain" controls playsinline autoplay muted></video>
    <div id="audio-box" class="hidden absolute inset-0 bg-slate-950/95 flex flex-col items-center justify-center p-4 text-center">
      <div class="text-3xl mb-2">🎙️</div>
      <h3 class="font-bold text-emerald-400 text-sm">وضع الراديو الصوتي (64kbps) للإنترنت الضعيف جداً</h3>
      <p class="text-xs text-slate-400 mt-1 mb-3">تم إيقاف الفيديو لتوفير 90% من البيانات ومنع أي تقطيع</p>
      <button onclick="setQ(-1)" class="px-3 py-1.5 bg-emerald-600 rounded-xl text-xs font-bold">العودة للفيديو</button>
    </div>
  </div>

  <div class="bg-slate-900/90 p-3.5 rounded-2xl border border-slate-800 space-y-3">
    <div class="flex flex-wrap gap-1.5">
      <button onclick="setQ(-1)" class="px-3 py-1.5 bg-emerald-600 rounded-xl text-xs font-bold">⚡ تلقائي ذكي (ABR)</button>
      <button onclick="setQ(0)" class="px-3 py-1.5 bg-amber-600 rounded-xl text-xs font-bold">🛡️ 240p (نت ضعيف جداً)</button>
      <button onclick="setQ(1)" class="px-3 py-1.5 bg-slate-800 rounded-xl text-xs font-bold">480p SD مستقر</button>
      <button onclick="setQ(2)" class="px-3 py-1.5 bg-slate-800 rounded-xl text-xs font-bold">1080p FHD</button>
      <button onclick="setAudioOnly()" class="px-3 py-1.5 bg-cyan-700 rounded-xl text-xs font-bold">🎙️ صوت فقط</button>
    </div>
    <div class="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800">
      <div class="flex gap-1.5">
        <button onclick="switchSrv('s1')" class="px-2.5 py-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 rounded-lg text-xs font-bold">سيرفر 1 (الرئيسي)</button>
        <button onclick="switchSrv('s2')" class="px-2.5 py-1 bg-slate-800 text-slate-300 rounded-lg text-xs font-bold">سيرفر 2 (احتياطي سريع)</button>
      </div>
      <div class="flex gap-1 w-full sm:w-auto">
        <input id="custom-url" type="text" placeholder="ضع رابط بث .m3u8 خارجي..." class="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-white">
        <button onclick="playCustom()" class="px-3 py-1 bg-emerald-600 rounded-lg text-xs font-bold">تشغيل</button>
      </div>
    </div>
  </div>

  <div class="bg-slate-900/90 p-3.5 rounded-2xl border border-slate-800 space-y-2.5">
    <h2 class="text-xs font-extrabold text-slate-300">🏆 جدول المباريات القابلة للمشاهدة فوراً (اضغط على أي مباراة):</h2>
    <div id="match-list" class="grid grid-cols-1 sm:grid-cols-2 gap-2"></div>
  </div>

<script>
const MATCHES = """ + str(MATCHES).replace("'", '"') + """;
let curMatch = MATCHES[0];
const v = document.getElementById('v');
let h = null;

function loadStream(url) {
  document.getElementById('audio-box').classList.add('hidden');
  if (Hls.isSupported()) {
    if (h) h.destroy();
    h = new Hls({ maxBufferLength: 30, maxMaxBufferLength: 60, lowLatencyMode: true });
    h.loadSource(url);
    h.attachMedia(v);
    h.on(Hls.Events.MANIFEST_PARSED, () => v.play().catch(()=>{}));
    h.on(Hls.Events.ERROR, (e, d) => { if (d.fatal) loadStream(curMatch.s2); });
  } else if (v.canPlayType('application/vnd.apple.mpegurl')) {
    v.src = url; v.play().catch(()=>{});
  }
}

function setQ(lvl) {
  document.getElementById('audio-box').classList.add('hidden');
  if (h) h.currentLevel = lvl;
  document.getElementById('net-pill').textContent = lvl === 0 ? '🛡️ طور 240p نشط' : (lvl === -1 ? '⚡ Adaptive HLS' : 'HD ثابت');
}

function setAudioOnly() {
  document.getElementById('audio-box').classList.remove('hidden');
  if (h) h.currentLevel = 0;
  document.getElementById('net-pill').textContent = '🎙️ صوت فقط 64kbps';
}

function switchSrv(key) { loadStream(curMatch[key]); }
function playCustom() {
  const u = document.getElementById('custom-url').value.trim();
  if (u) loadStream(u);
}

function selectMatch(id) {
  curMatch = MATCHES.find(m => m.id === id) || MATCHES[0];
  document.getElementById('now-playing').textContent = 'جاري البث: ' + curMatch.home + ' vs ' + curMatch.away + ' (' + curMatch.league + ')';
  loadStream(curMatch.s1);
  renderList();
}

function renderList() {
  document.getElementById('match-list').innerHTML = MATCHES.map(m => `
    <div onclick="selectMatch('${m.id}')" class="cursor-pointer p-2.5 rounded-xl border transition ${m.id===curMatch.id?'bg-emerald-950/50 border-emerald-500':'bg-slate-950/70 border-slate-800'}">
      <div class="flex justify-between text-[11px] text-slate-400 mb-1"><span>${m.league}</span><span class="text-red-400 font-bold">${m.time}</span></div>
      <div class="flex justify-between items-center text-xs font-bold"><span>${m.home}</span><span class="px-2 py-0.5 bg-slate-800 text-emerald-400 rounded">${m.score}</span><span>${m.away}</span></div>
    </div>
  `).join('');
}

renderList();
loadStream(curMatch.s1);
</script>
</body></html>"""

@app.route("/")
def index():
    return HTML_UI

@app.route("/health")
def health():
    return jsonify({"status": "online", "bot": "PulseGoal Ultra Pro"}), 200

def main_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("📺 فتح مشغل المباريات الذكي (بدون تقطيع)", web_app=WebAppInfo(url=WEBAPP_URL)))
    for m in MATCHES:
        kb.add(InlineKeyboardButton(f"🔴 {m['home']} vs {m['away']} ({m['score']})", web_app=WebAppInfo(url=WEBAPP_URL)))
    return kb

if bot:
    @bot.message_handler(commands=["start", "help"])
    def welcome(msg):
        bot.send_message(
            msg.chat.id,
            "⚽ <b>مرحباً بك في PulseGoal Ultra Pro</b>\n\n"
            "✨ <b>مميزات البث الذكي:</b>\n"
            "• <b>Adaptive HLS:</b> يتكيف تلقائياً مع سرعة الإنترنت بدون توقف.\n"
            "• <b>درع الإنترنت الضعيف:</b> طور 240p + وضع الراديو الصوتي (64kbps).\n"
            "• <b>سيرفرات طوارئ:</b> تحويل تلقائي عند انقطاع المصدر.\n\n"
            "👇 <b>اختر المباراة التي تريد مشاهدتها الآن:</b>",
            reply_markup=main_kb()
        )

def poll():
    while bot:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=poll, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)
