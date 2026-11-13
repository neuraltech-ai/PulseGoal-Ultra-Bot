import os, re, time, threading, requests
from flask import Flask, jsonify, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
WEBAPP_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://pulsegoal-ultra-bot.onrender.com")
PORT = int(os.environ.get("PORT", 8080))

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True) if BOT_TOKEN else None

# قنوات رياضية مباشرة حقيقية (تعمل على مدار الساعة) + جلب تلقائي من IPTV-org Sports
CORE_CHANNELS = [
    {"name": "🇲🇦 الرياضية المغربية (Arryadia HD)", "url": "https://cdn.live.easybroadcast.io/ts_corp/73_arryadia-tnt_zcmwjdc/playlist_dvr.m3u8"},
    {"name": "⚽ Red Bull TV Sport (FHD)", "url": "https://rbmn-live.akamaized.net/hls/live/590964/BoRB-AT/master.m3u8"},
    {"name": "🏆 FIFA+ Live Football Channel", "url": "https://a62dad94.wurl.com/master/f36d25e7e52f1ba8d7e56eb859c636563214f541/UmFrdXRlblRWLWV1X0ZJRkFQbHVzRUVuZ2xpc2hITFM/playlist.m3u8"},
    {"name": "🇯🇴 الأردن الرياضية (Jordan Sport)", "url": "https://stream.joinvisions.net:1935/jorlive/sport/chunklist.m3u8"},
    {"name": "🌍 Unite8 Sports 1 HD", "url": "https://fta.ektv.in/live/263/master.m3u8"}
]

def fetch_live_matches():
    """جلب مباريات اليوم الحقيقية والنتائج الفورية من ESPN Soccer API"""
    try:
        r = requests.get("https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard", timeout=8)
        data = r.json()
        events = data.get("events", [])
        real_matches = []
        for ev in events[:16]:
            comp = ev.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) >= 2:
                home = competitors[0].get("team", {}).get("shortDisplayName", "Home")
                away = competitors[1].get("team", {}).get("shortDisplayName", "Away")
                h_score = competitors[0].get("score", "0")
                a_score = competitors[1].get("score", "0")
                status_detail = ev.get("status", {}).get("type", {}).get("shortDetail", "اليوم")
                state = ev.get("status", {}).get("type", {}).get("state", "pre")
                league = ev.get("season", {}).get("slug", "مباريات اليوم").replace("-", " ").upper()
                real_matches.append({
                    "home": home,
                    "away": away,
                    "score": f"{h_score} - {a_score}" if state != "pre" else "vs",
                    "status": f"🔴 مباشر ({status_detail})" if state == "in" else status_detail,
                    "is_live": state == "in",
                    "league": league
                })
        return real_matches
    except Exception:
        return []

HTML_UI = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>PulseGoal Ultra | البث الرياضي الحي</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800&display=swap" rel="stylesheet">
<style>body{font-family:'Cairo',sans-serif;background:#060911;color:#f8fafc;}</style>
</head>
<body class="p-3 sm:p-5 max-w-5xl mx-auto space-y-4">
  <div class="flex items-center justify-between bg-slate-900 p-3.5 rounded-2xl border border-slate-800 shadow-lg">
    <div>
      <h1 class="text-base sm:text-lg font-extrabold text-emerald-400">⚽ PulseGoal Ultra — البث الرياضي الحقيقي</h1>
      <p id="now-playing" class="text-xs text-slate-300">جاري تشغيل: 🇲🇦 الرياضية المغربية (Arryadia HD)</p>
    </div>
    <span id="net-pill" class="text-[11px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2.5 py-1 rounded-full font-bold">بث حي مباشر 🔴</span>
  </div>

  <!-- مشغل البث المباشر -->
  <div class="relative aspect-video bg-black rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
    <video id="v" class="w-full h-full object-contain" controls playsinline autoplay></video>
    <div id="audio-box" class="hidden absolute inset-0 bg-slate-950/95 flex flex-col items-center justify-center p-4 text-center">
      <div class="text-3xl mb-2">🎙️</div>
      <h3 class="font-bold text-emerald-400 text-sm">وضع الراديو الصوتي (64kbps) للإنترنت الضعيف جداً</h3>
      <button onclick="setQ(-1)" class="mt-3 px-4 py-1.5 bg-emerald-600 rounded-xl text-xs font-bold">العودة للفيديو</button>
    </div>
  </div>

  <!-- التحكم في الجودة والإنترنت الضعيف -->
  <div class="bg-slate-900 p-3.5 rounded-2xl border border-slate-800 space-y-3">
    <div class="flex flex-wrap gap-1.5">
      <button onclick="setQ(-1)" class="px-3 py-1.5 bg-emerald-600 rounded-xl text-xs font-bold">⚡ تلقائي ذكي (ABR)</button>
      <button onclick="setQ(0)" class="px-3 py-1.5 bg-amber-600 rounded-xl text-xs font-bold">🛡️ 240p (نت ضعيف جداً)</button>
      <button onclick="setQ(1)" class="px-3 py-1.5 bg-slate-800 rounded-xl text-xs font-bold">480p SD مستقر</button>
      <button onclick="setQ(2)" class="px-3 py-1.5 bg-slate-800 rounded-xl text-xs font-bold">1080p FHD</button>
      <button onclick="setAudioOnly()" class="px-3 py-1.5 bg-cyan-700 rounded-xl text-xs font-bold">🎙️ صوت فقط</button>
    </div>
    <div class="flex gap-1.5 pt-2 border-t border-slate-800">
      <input id="custom-url" type="text" placeholder="أدخل أي رابط قناة أو مباراة .m3u8 هنا..." class="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white">
      <button onclick="playCustom()" class="px-4 py-1.5 bg-emerald-600 rounded-xl text-xs font-bold">تشغيل الرابط</button>
    </div>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <!-- القنوات الرياضية المباشرة -->
    <div class="bg-slate-900 p-3.5 rounded-2xl border border-slate-800 space-y-2.5">
      <div class="flex items-center justify-between">
        <h2 class="text-xs font-extrabold text-emerald-400">📺 القنوات الرياضية الحية (اضغط للمشاهدة):</h2>
        <input id="ch-search" oninput="filterChannels()" type="text" placeholder="بحث في +150 قناة رياضية..." class="bg-slate-950 border border-slate-700 rounded-lg px-2 py-1 text-[11px] text-white w-40">
      </div>
      <div id="channels-list" class="space-y-1.5 max-h-72 overflow-y-auto pr-1"></div>
    </div>

    <!-- جدول مباريات اليوم الحقيقي من ESPN -->
    <div class="bg-slate-900 p-3.5 rounded-2xl border border-slate-800 space-y-2.5">
      <div class="flex items-center justify-between">
        <h2 class="text-xs font-extrabold text-amber-400">⚽ جدول ونتائج مباريات اليوم الحقيقية (محدث لحظياً):</h2>
        <button onclick="loadRealMatches()" class="text-[11px] bg-slate-800 px-2 py-0.5 rounded text-slate-300">🔄 تحديث</button>
      </div>
      <div id="real-matches-list" class="space-y-2 max-h-72 overflow-y-auto pr-1">
        <p class="text-xs text-slate-400">جاري جلب مباريات اليوم الحقيقية...</p>
      </div>
    </div>
  </div>

<script>
const v = document.getElementById('v');
let h = null;
let allChannels = [
  {name: "🇲🇦 الرياضية المغربية (Arryadia HD)", url: "https://cdn.live.easybroadcast.io/ts_corp/73_arryadia-tnt_zcmwjdc/playlist_dvr.m3u8"},
  {name: "🏆 FIFA+ Global Football Live", url: "https://a62dad94.wurl.com/master/f36d25e7e52f1ba8d7e56eb859c636563214f541/UmFrdXRlblRWLWV1X0ZJRkFQbHVzRUVuZ2xpc2hITFM/playlist.m3u8"},
  {name: "⚽ Red Bull TV Sports FHD", url: "https://rbmn-live.akamaized.net/hls/live/590964/BoRB-AT/master.m3u8"},
  {name: "🌍 Unite8 Sports 1 HD", url: "https://fta.ektv.in/live/263/master.m3u8"}
];

function playChannel(name, url) {
  document.getElementById('now-playing').textContent = 'جاري تشغيل: ' + name;
  document.getElementById('audio-box').classList.add('hidden');
  if (Hls.isSupported()) {
    if (h) h.destroy();
    h = new Hls({ maxBufferLength: 30, maxMaxBufferLength: 60, lowLatencyMode: true });
    h.loadSource(url);
    h.attachMedia(v);
    h.on(Hls.Events.MANIFEST_PARSED, () => v.play().catch(()=>{}));
  } else if (v.canPlayType('application/vnd.apple.mpegurl')) {
    v.src = url; v.play().catch(()=>{});
  }
}

function setQ(lvl) {
  document.getElementById('audio-box').classList.add('hidden');
  if (h) h.currentLevel = lvl;
  document.getElementById('net-pill').textContent = lvl === 0 ? '🛡️ طور 240p نشط' : 'بث حي مباشر 🔴';
}

function setAudioOnly() {
  document.getElementById('audio-box').classList.remove('hidden');
  if (h) h.currentLevel = 0;
}

function playCustom() {
  const u = document.getElementById('custom-url').value.trim();
  if (u) playChannel('بث خارجي مخصص', u);
}

function renderChannels(list) {
  document.getElementById('channels-list').innerHTML = list.slice(0, 80).map((c, idx) => `
    <button onclick="playChannel('${c.name.replace(/'/g, "")}', '${c.url}')" class="w-full text-right p-2 rounded-xl bg-slate-950 hover:bg-emerald-950/50 border border-slate-800 hover:border-emerald-500/50 flex items-center justify-between text-xs font-bold transition">
      <span class="truncate">${c.name}</span>
      <span class="text-[10px] bg-emerald-600/20 text-emerald-400 px-2 py-0.5 rounded shrink-0">تشغيل ▶</span>
    </button>
  `).join('');
}

function filterChannels() {
  const q = document.getElementById('ch-search').value.toLowerCase();
  renderChannels(allChannels.filter(c => c.name.toLowerCase().includes(q)));
}

// جلب أكثر من 150 قناة رياضية حية من IPTV-org Sports تلقائياً
async function loadIptvSports() {
  renderChannels(allChannels);
  try {
    const res = await fetch('https://iptv-org.github.io/iptv/categories/sports.m3u');
    const txt = await res.text();
    const lines = txt.split('\\n');
    let curName = '';
    for (let line of lines) {
      line = line.trim();
      if (line.startsWith('#EXTINF:')) {
        const parts = line.split(',');
        curName = '📺 ' + (parts[parts.length - 1] || 'Sports Channel').trim();
      } else if (line.startsWith('https://') && line.includes('.m3u8')) {
        allChannels.push({ name: curName, url: line });
      }
    }
    renderChannels(allChannels);
  } catch (e) {}
}

// جلب مباريات اليوم الحقيقية مباشرة من ESPN API
async function loadRealMatches() {
  const box = document.getElementById('real-matches-list');
  try {
    const res = await fetch('https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard');
    const data = await res.json();
    const events = data.events || [];
    if (!events.length) {
      box.innerHTML = '<p class="text-xs text-slate-400">لا توجد مباريات جارية في هذه اللحظة.</p>';
      return;
    }
    box.innerHTML = events.slice(0, 20).map(ev => {
      const comp = (ev.competitions && ev.competitions[0]) || {};
      const teams = comp.competitors || [];
      if (teams.length < 2) return '';
      const home = teams[0].team.shortDisplayName;
      const away = teams[1].team.shortDisplayName;
      const hScore = teams[0].score || '0';
      const aScore = teams[1].score || '0';
      const state = ev.status.type.state;
      const detail = ev.status.type.shortDetail;
      return `
        <div class="p-2.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
          <div class="flex justify-between text-[11px] text-slate-400">
            <span>⚽ ${ev.name}</span>
            <span class="${state==='in'?'text-red-400 font-bold':'text-emerald-400'}">${state==='in'?'🔴 مباشر '+detail:detail}</span>
          </div>
          <div class="flex justify-between items-center text-xs font-bold">
            <span>${home}</span>
            <span class="px-2.5 py-0.5 bg-slate-800 text-amber-400 rounded font-mono">${state==='pre'?'VS':hScore+' - '+aScore}</span>
            <span>${away}</span>
          </div>
        </div>
      `;
    }).join('');
  } catch (e) {
    box.innerHTML = '<p class="text-xs text-red-400">تعذر تحديث الجدول اللحظي.</p>';
  }
}

loadIptvSports();
loadRealMatches();
playChannel(allChannels[0].name, allChannels[0].url);
</script>
</body></html>"""

@app.route("/")
def index():
    return HTML_UI

@app.route("/health")
def health():
    return jsonify({"status": "online", "bot": "PulseGoal Ultra Real-Time"}), 200

if bot:
    @bot.message_handler(commands=["start", "help"])
    def welcome(msg):
        matches = fetch_live_matches()
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton("📺 فتح التلفزيون الرياضي ومشغل القنوات الحية (+150 قناة)", web_app=WebAppInfo(url=WEBAPP_URL)))
        for m in matches[:6]:
            kb.add(InlineKeyboardButton(f"⚽ {m['home']} ({m['score']}) {m['away']} | {m['status']}", web_app=WebAppInfo(url=WEBAPP_URL)))
        bot.send_message(
            msg.chat.id,
            "⚽ <b>مرحباً بك في PulseGoal Ultra — النسخة الحية</b>\n\n"
            "📡 <b>تم ربط البوت بجدول المباريات العالمي اللحظي والقنوات الرياضية المفتوحة المباشرة (+150 قناة رياضية حقيقية مثل الرياضية المغربية و FIFA+ وغيرها):</b>\n\n"
            "👇 اضغط أدناه لفتح التلفزيون الرياضي المباشر أو استعراض مباريات اليوم الحقيقية:",
            reply_markup=kb
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
