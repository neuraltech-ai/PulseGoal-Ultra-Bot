import os, re, time, urllib.parse, threading, requests
from flask import Flask, jsonify, request, Response
import telebot
from telebot.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
WEBAPP_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://pulsegoal-ultra-bot.onrender.com")
PORT = int(os.environ.get("PORT", 8080))

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True) if BOT_TOKEN else None

# قائمة الدوريات العالمية والعربية والأفريقية الشاملة (ESPN Multi-League Engine)
LEAGUES = [
    ("all", "🌍 كل المباريات الجارية"),
    ("uefa.champions", "🏆 دوري أبطال أوروبا"),
    ("uefa.europa", "🟠 الدوري الأوروبي"),
    ("eng.1", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 الدوري الإنجليزي الممتاز"),
    ("esp.1", "🇪🇸 الدوري الإسباني LaLiga"),
    ("ita.1", "🇮🇹 الدوري الإيطالي Serie A"),
    ("ger.1", "🇩🇪 الدوري الألماني Bundesliga"),
    ("fra.1", "🇫🇷 الدوري الفرنسي Ligue 1"),
    ("caf.nations", "🌍 تصفيات وبطولات أفريقيا CAF"),
    ("caf.champions", "🌍 دوري أبطال أفريقيا"),
    ("caf.confed", "🇲🇦 كأس الكونفدرالية الأفريقية"),
    ("fifa.worldq.caf", "🌍 تصفيات كأس العالم - أفريقيا"),
    ("fifa.worldq.uefa", "🇪🇺 تصفيات كأس العالم - أوروبا"),
    ("fifa.worldq.conmebol", "🌎 تصفيات أمريكا الجنوبية"),
    ("ksa.1", "🇸🇦 دوري روشن السعودي")
]

# باقة القنوات الرياضية العربية والعالمية مع سيرفرات متعددة وبروكسي مضاد للتقطيع
VERIFIED_CHANNELS = [
    {"id": "ch1", "cat": "arab", "name": "🇲🇦 الرياضية المغربية (Arryadia TNT HD)", "url": "https://cdn.live.easybroadcast.io/ts_corp/73_arryadia-tnt_zcmwjdc/playlist_dvr.m3u8", "backup": "https://snrtlive.ma/ar/arryadia"},
    {"id": "ch2", "cat": "arab", "name": "🇶🇦 الكأس الرياضية 1 (Alkass One HD)", "url": "https://liveakgr.alkassdigital.net/hls/live/2097037/Alkass5/master.m3u8", "backup": "https://www.alkass.net/alkass/live.aspx?ch=one"},
    {"id": "ch3", "cat": "arab", "name": "🇦🇪 أبوظبي الرياضية 1 (AD Sports 1 HD)", "url": "https://admdn1.cdn.mangomolo.com/adsports1/smil:adsports1.stream.smil/playlist.m3u8", "backup": "https://adsports.ae/live/154/"},
    {"id": "ch4", "cat": "arab", "name": "🇦🇪 دبي الرياضية 1 (Dubai Sports 1 FHD)", "url": "https://dmitnthvll.cdn.mangomolo.com/dubaisports/smil:dubaisports.stream.smil/playlist.m3u8", "backup": "https://www.dubaisports.ae/content/dubaisports/livestreaming/channel-1.html"},
    {"id": "ch5", "cat": "arab", "name": "🇰🇼 الكويت الرياضية (Kuwait Sport HD)", "url": "https://kwmedia.hibridcdn.net/kwmedia/kwtv3/playlist.m3u8", "backup": "https://media.gov.kw"},
    {"id": "ch6", "cat": "arab", "name": "🇴🇲 عمان الرياضية (Oman Sport HD)", "url": "https://partneta.cdn.mgmlcdn.com/omsport/smil:omsport.stream.smil/playlist.m3u8", "backup": "https://ain.om"},
    {"id": "ch7", "cat": "arab", "name": "🇧🇭 البحرين الرياضية 1 (Bahrain Sport HD)", "url": "https://5c7b683162943.streamlock.net/live/ngrp:bahrainsport1_all/playlist.m3u8", "backup": "https://www.bahrain.bh"},
    {"id": "ch8", "cat": "arab", "name": "🇯🇴 الأردن الرياضية (Jordan Sport HD)", "url": "https://stream.joinvisions.net:1935/jorlive/sport/chunklist.m3u8", "backup": "https://www.jrtv.gov.jo"},
    {"id": "ch9", "cat": "global", "name": "🏆 FIFA+ Global Football TV (FHD)", "url": "https://a62dad94.wurl.com/master/f36d25e7e52f1ba8d7e56eb859c636563214f541/UmFrdXRlblRWLWV1X0ZJRkFQbHVzRUVuZ2xpc2hITFM/playlist.m3u8", "backup": "https://www.plus.fifa.com"},
    {"id": "ch10", "cat": "global", "name": "⚽ Red Bull Sports TV (1080p FHD)", "url": "https://rbmn-live.akamaized.net/hls/live/590964/BoRB-AT/master.m3u8", "backup": "https://www.redbull.com"},
    {"id": "ch11", "cat": "global", "name": "🌍 Unite8 Sports 1 HD (1080p)", "url": "https://fta.ektv.in/live/263/master.m3u8", "backup": "https://fta.ektv.in/live/263/master.m3u8"},
    {"id": "ch12", "cat": "global", "name": "🇪🇸 Real Madrid TV (Official Live)", "url": "https://rmtv.akamaized.net/hls/live/2043153/rmtv-es-web/master.m3u8", "backup": "https://www.realmadrid.com/real-madrid-tv"}
]

MATCH_CACHE = {"ts": 0, "data": []}

def fetch_all_world_matches(league_code="all"):
    """جلب جميع المباريات العالمية والعربية مع القنوات الناقلة والتوقيت الدقيق"""
    now = time.time()
    if league_code == "all" and now - MATCH_CACHE["ts"] < 45 and MATCH_CACHE["data"]:
        return MATCH_CACHE["data"]

    codes_to_query = [league_code] if league_code != "all" else [
        "all", "uefa.champions", "eng.1", "esp.1", "ita.1", "ger.1", "fra.1",
        "caf.nations", "caf.champions", "caf.confed", "fifa.worldq.caf", "fifa.worldq.uefa", "ksa.1"
    ]
    seen_ids = set()
    results = []

    for code in codes_to_query:
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard"
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                continue
            js = r.json()
            league_name = (js.get("leagues", [{}])[0].get("name")) or code.upper()
            for ev in js.get("events", []):
                ev_id = ev.get("id")
                if not ev_id or ev_id in seen_ids:
                    continue
                seen_ids.add(ev_id)
                comp = (ev.get("competitions") or [{}])[0]
                competitors = comp.get("competitors") or []
                if len(competitors) < 2:
                    continue
                home = competitors[0].get("team", {}).get("shortDisplayName", "Home")
                away = competitors[1].get("team", {}).get("shortDisplayName", "Away")
                h_logo = competitors[0].get("team", {}).get("logo", "")
                a_logo = competitors[1].get("team", {}).get("logo", "")
                h_score = competitors[0].get("score", "0")
                a_score = competitors[1].get("score", "0")
                state = ev.get("status", {}).get("type", {}).get("state", "pre")
                detail = ev.get("status", {}).get("type", {}).get("shortDetail", "")

                # استخراج القنوات الناقلة الرسمية من بيانات المباراة أو تعيين القنوات الرياضية المناسبة
                broadcasts = []
                for b in comp.get("broadcasts", []):
                    broadcasts.extend(b.get("names", []))
                for gb in comp.get("geoBroadcasts", []):
                    media_name = gb.get("media", {}).get("shortName")
                    if media_name:
                        broadcasts.append(media_name)
                broadcaster_str = " | ".join(list(dict.fromkeys(broadcasts))[:3]) if broadcasts else "beIN / الرياضية / FIFA+"

                results.append({
                    "id": ev_id,
                    "league": league_name,
                    "home": home,
                    "away": away,
                    "h_logo": h_logo,
                    "a_logo": a_logo,
                    "score": f"{h_score} - {a_score}" if state != "pre" else "VS",
                    "status": f"🔴 مباشر ({detail})" if state == "in" else ("✅ انتهت" if state == "post" else f"🕒 {detail}"),
                    "state": state,
                    "broadcaster": broadcaster_str
                })
        except Exception:
            continue

    # ترتيب المباريات: المباشر أولاً ثم القادمة ثم المنتهية
    order_map = {"in": 0, "pre": 1, "post": 2}
    results.sort(key=lambda x: order_map.get(x["state"], 3))

    if league_code == "all" and results:
        MATCH_CACHE["ts"] = now
        MATCH_CACHE["data"] = results
    return results

@app.route("/api/matches")
def api_matches():
    league = request.args.get("league", "all")
    return jsonify(fetch_all_world_matches(league))

@app.route("/api/channels")
def api_channels():
    return jsonify(VERIFIED_CHANNELS)

@app.route("/proxy/stream")
def proxy_stream():
    """
    محرك بروكسي ذكي (Anti-CORS & Anti-Freeze HLS Rewrite Proxy)
    يحل مشكلة توقف القنوات في متصفح تيليغرام عبر جلب ملفات m3u8 والقطع TS وتمريرها عبر السيرفر.
    """
    target_url = request.args.get("url", "")
    if not target_url:
        return "Missing url", 400
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
            "Referer": urllib.parse.urljoin(target_url, "/"),
            "Origin": urllib.parse.urljoin(target_url, "/")[:-1],
            "Connection": "keep-alive"
        }
        r = requests.get(target_url, headers=headers, timeout=12, verify=False)
        ctype = r.headers.get("Content-Type", "")
        if "mpegurl" in ctype.lower() or target_url.split("?")[0].endswith(".m3u8") or b"#EXTM3U" in r.content[:50]:
            text = r.text
            base_url = target_url.rsplit("/", 1)[0] + "/"
            rewritten_lines = []
            for line in text.splitlines():
                sline = line.strip()
                if sline and not sline.startswith("#"):
                    abs_url = urllib.parse.urljoin(base_url, sline)
                    rewritten_lines.append(f"/proxy/stream?url={urllib.parse.quote(abs_url, safe='')}")
                else:
                    rewritten_lines.append(line)
            body = "\n".join(rewritten_lines)
            return Response(
                body,
                status=200,
                content_type="application/vnd.apple.mpegurl",
                headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "no-cache"}
            )
        else:
            return Response(
                r.content,
                status=r.status_code,
                content_type=ctype or "video/MP2T",
                headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "public, max-age=10"}
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 502

HTML_UI = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>PulseGoal Ultra Global</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800;900&display=swap" rel="stylesheet">
<style>
  body { font-family: 'Cairo', sans-serif; background: #050811; color: #f8fafc; }
  .glass { background: rgba(15, 23, 42, 0.88); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.08); }
  ::-webkit-scrollbar { width: 5px; height: 5px; }
  ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 99px; }
</style>
</head>
<body class="p-2.5 sm:p-4 max-w-6xl mx-auto space-y-3.5">

  <!-- الهيدر الاحترافي -->
  <div class="glass p-3.5 rounded-2xl flex flex-wrap items-center justify-between gap-2 shadow-xl border-r-4 border-r-emerald-500">
    <div class="flex items-center gap-2.5">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 flex items-center justify-center font-black text-white shadow-lg">PG</div>
      <div>
        <h1 class="text-sm sm:text-base font-black text-white">PulseGoal <span class="text-emerald-400">Global Ultra</span></h1>
        <p id="now-playing" class="text-[11px] text-emerald-300 font-bold">جاري البث عبر السيرفر الذكي المضاد للتقطيع</p>
      </div>
    </div>
    <div class="flex items-center gap-1.5">
      <button onclick="toggleProxyMode()" id="proxy-btn" class="text-[11px] bg-emerald-600 text-white px-2.5 py-1 rounded-xl font-bold shadow">🛡️ درع البروكسي: مفعل</button>
      <span id="status-badge" class="text-[11px] bg-red-500/20 text-red-300 border border-red-500/30 px-2.5 py-1 rounded-xl font-bold">LIVE 🔴</span>
    </div>
  </div>

  <!-- مشغل البث الذكي مع Auto-Failover -->
  <div class="relative aspect-video bg-black rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
    <video id="v" class="w-full h-full object-contain bg-black" controls playsinline autoplay></video>
    <div id="audio-overlay" class="hidden absolute inset-0 bg-slate-950/95 flex flex-col items-center justify-center p-4 text-center z-20">
      <div class="text-4xl mb-2 animate-bounce">🎙️</div>
      <h3 class="font-extrabold text-emerald-400 text-sm">وضع الراديو الصوتي الفائق (64kbps)</h3>
      <p class="text-xs text-slate-400 mt-1 mb-3">يعمل بدون أي تقطيع على أضعف شبكات الإنترنت (2G/3G)</p>
      <button onclick="setQ(-1)" class="px-4 py-1.5 bg-emerald-600 rounded-xl text-xs font-bold">العودة لبث الفيديو</button>
    </div>
  </div>

  <!-- أزرار التحكم بالجودة والسيرفرات (بأسلوب Gemini Global) -->
  <div class="glass p-3 rounded-2xl space-y-2.5">
    <div class="flex flex-wrap items-center justify-between gap-1.5">
      <div class="flex flex-wrap gap-1.5">
        <button onclick="setQ(-1)" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-xs font-bold">⚡ تلقائي ذكي (ABR)</button>
        <button onclick="setQ(0)" class="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 rounded-xl text-xs font-bold">🛡️ 240p (نت ضعيف)</button>
        <button onclick="setQ(1)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-xl text-xs font-bold">480p SD مستقر</button>
        <button onclick="setQ(2)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-xl text-xs font-bold">1080p FHD</button>
        <button onclick="setAudioMode()" class="px-3 py-1.5 bg-cyan-700 hover:bg-cyan-600 rounded-xl text-xs font-bold">🎙️ راديو صوتي</button>
      </div>
      <button onclick="openExternalBackup()" class="px-3 py-1.5 bg-purple-700 hover:bg-purple-600 rounded-xl text-xs font-bold">🌐 فتح المصدر الاحتياطي المباشر</button>
    </div>
    <div class="flex gap-1.5 pt-2 border-t border-slate-800/80">
      <input id="custom-m3u8" type="text" placeholder="الصق أي رابط بث مباشر .m3u8 لتشغيله عبر درع البروكسي..." class="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white">
      <button onclick="playCustomUrl()" class="px-4 py-1.5 bg-emerald-600 rounded-xl text-xs font-bold shrink-0">تشغيل فوري</button>
    </div>
  </div>

  <!-- تبويبات التبديل السريع بين مركز المباريات الشامل والتلفزيون الرياضي -->
  <div class="grid grid-cols-2 gap-2">
    <button id="tab-btn-matches" onclick="switchTab('matches')" class="py-2.5 rounded-xl font-extrabold text-xs bg-emerald-600 text-white shadow-lg">⚽ جميع مباريات اليوم والقنوات الناقلة</button>
    <button id="tab-btn-channels" onclick="switchTab('channels')" class="py-2.5 rounded-xl font-extrabold text-xs bg-slate-900 text-slate-300 border border-slate-800">📺 باقة القنوات الرياضية الحية</button>
  </div>

  <!-- قسم جميع المباريات العالمية والعربية -->
  <div id="sec-matches" class="glass p-3.5 rounded-2xl space-y-3">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <div class="flex items-center gap-1.5 overflow-x-auto pb-1 max-w-full">
        <button onclick="loadMatches('all')" class="px-2.5 py-1 rounded-lg bg-emerald-600 text-[11px] font-bold shrink-0">🌍 الكل</button>
        <button onclick="loadMatches('uefa.champions')" class="px-2.5 py-1 rounded-lg bg-slate-800 text-[11px] font-bold shrink-0">🏆 أبطال أوروبا</button>
        <button onclick="loadMatches('eng.1')" class="px-2.5 py-1 rounded-lg bg-slate-800 text-[11px] font-bold shrink-0">🏴󠁧󠁢󠁥󠁮󠁧󠁿 الإنجليزي</button>
        <button onclick="loadMatches('esp.1')" class="px-2.5 py-1 rounded-lg bg-slate-800 text-[11px] font-bold shrink-0">🇪🇸 الإسباني</button>
        <button onclick="loadMatches('caf.nations')" class="px-2.5 py-1 rounded-lg bg-slate-800 text-[11px] font-bold shrink-0">🌍 أفريقيا</button>
        <button onclick="loadMatches('ksa.1')" class="px-2.5 py-1 rounded-lg bg-slate-800 text-[11px] font-bold shrink-0">🇸🇦 السعودي</button>
      </div>
      <input id="match-search" oninput="filterMatches()" type="text" placeholder="ابحث عن فريق أو بطولة..." class="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1 text-xs text-white w-full sm:w-48">
    </div>
    <div id="matches-count" class="text-[11px] text-emerald-400 font-bold">جاري جلب جميع المباريات العالمية...</div>
    <div id="matches-grid" class="grid grid-cols-1 md:grid-cols-2 gap-2.5 max-h-[460px] overflow-y-auto pr-1"></div>
  </div>

  <!-- قسم القنوات الرياضية المفحوصة -->
  <div id="sec-channels" class="hidden glass p-3.5 rounded-2xl space-y-3">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <div class="flex gap-1.5">
        <button onclick="filterChCat('all')" class="px-3 py-1 rounded-lg bg-emerald-600 text-xs font-bold">كل القنوات</button>
        <button onclick="filterChCat('arab')" class="px-3 py-1 rounded-lg bg-slate-800 text-xs font-bold">🇲🇦🇶🇦🇦🇪 القنوات العربية</button>
        <button onclick="filterChCat('global')" class="px-3 py-1 rounded-lg bg-slate-800 text-xs font-bold">🌍 القنوات العالمية +150</button>
      </div>
      <input id="ch-search" oninput="renderChannels()" type="text" placeholder="ابحث عن قناة رياضية..." class="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1 text-xs text-white w-full sm:w-48">
    </div>
    <div id="channels-grid" class="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-[460px] overflow-y-auto pr-1"></div>
  </div>

<script>
const v = document.getElementById('v');
let h = null;
let useProxy = true;
let curChannel = null;
let allMatches = [];
let allChannels = [];
let curChCat = 'all';

function switchTab(t) {
  document.getElementById('sec-matches').classList.toggle('hidden', t !== 'matches');
  document.getElementById('sec-channels').classList.toggle('hidden', t !== 'channels');
  document.getElementById('tab-btn-matches').className = t === 'matches' ? 'py-2.5 rounded-xl font-extrabold text-xs bg-emerald-600 text-white shadow-lg' : 'py-2.5 rounded-xl font-extrabold text-xs bg-slate-900 text-slate-300 border border-slate-800';
  document.getElementById('tab-btn-channels').className = t === 'channels' ? 'py-2.5 rounded-xl font-extrabold text-xs bg-emerald-600 text-white shadow-lg' : 'py-2.5 rounded-xl font-extrabold text-xs bg-slate-900 text-slate-300 border border-slate-800';
}

function toggleProxyMode() {
  useProxy = !useProxy;
  const btn = document.getElementById('proxy-btn');
  btn.textContent = useProxy ? '🛡️ درع البروكسي: مفعل' : '⚡ اتصال مباشر: مفعل';
  btn.className = useProxy ? 'text-[11px] bg-emerald-600 text-white px-2.5 py-1 rounded-xl font-bold shadow' : 'text-[11px] bg-amber-600 text-white px-2.5 py-1 rounded-xl font-bold shadow';
  if (curChannel) startStream(curChannel.name, curChannel.url, curChannel.backup, false);
}

function startStream(name, rawUrl, backupUrl, triedFallback) {
  curChannel = { name, url: rawUrl, backup: backupUrl || rawUrl };
  document.getElementById('now-playing').textContent = '📺 جاري تشغيل: ' + name;
  document.getElementById('audio-overlay').classList.add('hidden');

  const finalUrl = (useProxy && !triedFallback) ? ('/proxy/stream?url=' + encodeURIComponent(rawUrl)) : rawUrl;

  if (Hls.isSupported()) {
    if (h) h.destroy();
    h = new Hls({ maxBufferLength: 35, maxMaxBufferLength: 60, enableWorker: true });
    h.loadSource(finalUrl);
    h.attachMedia(v);
    h.on(Hls.Events.MANIFEST_PARSED, () => { v.play().catch(()=>{}); });
    h.on(Hls.Events.ERROR, (ev, data) => {
      if (data.fatal) {
        if (!triedFallback) {
          // إذا تعثر البروكسي أو المباشر، يجرب الطريقة العكسية تلقائياً دون توقف
          startStream(name, rawUrl, backupUrl, true);
        }
      }
    });
  } else if (v.canPlayType('application/vnd.apple.mpegurl')) {
    v.src = finalUrl;
    v.play().catch(()=>{});
  }
}

function setQ(lvl) {
  document.getElementById('audio-overlay').classList.add('hidden');
  if (h) h.currentLevel = lvl;
}

function setAudioMode() {
  document.getElementById('audio-overlay').classList.remove('hidden');
  if (h) h.currentLevel = 0;
}

function openExternalBackup() {
  if (curChannel && curChannel.backup) window.open(curChannel.backup, '_blank');
}

function playCustomUrl() {
  const u = document.getElementById('custom-m3u8').value.trim();
  if (u) startStream('بث مخصص خارجي', u, u, false);
}

async function initChannels() {
  try {
    const res = await fetch('/api/channels');
    allChannels = await res.json();
    renderChannels();
    if (allChannels.length > 0) startStream(allChannels[8].name, allChannels[8].url, allChannels[8].backup, false);

    // إضافة قنوات HTTPS الرياضية العالمية من IPTV-org
    const iptv = await fetch('https://iptv-org.github.io/iptv/categories/sports.m3u');
    const txt = await iptv.text();
    const lines = txt.split('\\n');
    let cname = '';
    for (let l of lines) {
      l = l.trim();
      if (l.startsWith('#EXTINF:')) {
        const p = l.split(',');
        cname = '🌍 ' + (p[p.length - 1] || 'Sports HD').trim();
      } else if (l.startsWith('https://') && l.includes('.m3u8')) {
        allChannels.push({ id: 'g_' + allChannels.length, cat: 'global', name: cname, url: l, backup: l });
      }
    }
    renderChannels();
  } catch (e) {}
}

function filterChCat(c) { curChCat = c; renderChannels(); }

function renderChannels() {
  const q = (document.getElementById('ch-search').value || '').toLowerCase();
  const filtered = allChannels.filter(c => (curChCat === 'all' || c.cat === curChCat) && c.name.toLowerCase().includes(q));
  document.getElementById('channels-grid').innerHTML = filtered.slice(0, 120).map((c, idx) => `
    <div onclick="startStream('${c.name.replace(/'/g, "")}', '${c.url}', '${c.backup || c.url}', false)" class="cursor-pointer p-3 rounded-xl bg-slate-950/90 hover:bg-emerald-950/40 border border-slate-800 hover:border-emerald-500/60 flex items-center justify-between gap-2 transition">
      <span class="text-xs font-bold truncate">${c.name}</span>
      <span class="text-[10px] bg-emerald-600 text-white px-2.5 py-1 rounded-lg font-bold shrink-0">مشاهدة ▶</span>
    </div>
  `).join('');
}

async function loadMatches(leagueCode) {
  document.getElementById('matches-count').textContent = '⏳ جاري جلب جميع المباريات والقنوات الناقلة...';
  try {
    const res = await fetch('/api/matches?league=' + encodeURIComponent(leagueCode));
    allMatches = await res.json();
    filterMatches();
  } catch (e) {
    document.getElementById('matches-count').textContent = '⚠️ تعذر الاتصال بمزود النتائج.';
  }
}

function filterMatches() {
  const q = (document.getElementById('match-search').value || '').toLowerCase();
  const list = allMatches.filter(m =>
    m.home.toLowerCase().includes(q) ||
    m.away.toLowerCase().includes(q) ||
    m.league.toLowerCase().includes(q)
  );
  document.getElementById('matches-count').textContent = `✅ تم العثور على (${list.length}) مباراة في الجدول العالمي الشامل:`;
  document.getElementById('matches-grid').innerHTML = list.map(m => `
    <div onclick="switchTab('channels')" class="cursor-pointer p-3 rounded-xl bg-slate-950/90 hover:bg-slate-900 border ${m.state==='in'?'border-red-500/60':'border-slate-800'} space-y-2 transition">
      <div class="flex items-center justify-between text-[11px]">
        <span class="text-emerald-400 font-bold truncate">🏆 ${m.league}</span>
        <span class="${m.state==='in'?'bg-red-500/20 text-red-300 border border-red-500/40':'bg-slate-800 text-slate-300'} px-2 py-0.5 rounded-md font-bold shrink-0">${m.status}</span>
      </div>
      <div class="flex items-center justify-between text-xs sm:text-sm font-extrabold text-white py-1">
        <span class="w-2/5 text-right truncate">${m.home}</span>
        <span class="px-3 py-1 rounded-xl bg-slate-900 border border-slate-700 text-amber-400 font-mono">${m.score}</span>
        <span class="w-2/5 text-left truncate">${m.away}</span>
      </div>
      <div class="flex items-center justify-between pt-1.5 border-t border-slate-800/80 text-[11px] text-slate-400">
        <span>📡 القنوات الناقلة: <strong class="text-slate-200">${m.broadcaster}</strong></span>
        <span class="text-emerald-400 font-bold">فتح القنوات ▶</span>
      </div>
    </div>
  `).join('');
}

initChannels();
loadMatches('all');
</script>
</body></html>"""

@app.route("/")
def index():
    return HTML_UI

@app.route("/health")
def health():
    return jsonify({"status": "online", "bot": "PulseGoal Global Ultra v6.0"}), 200

# ==============================================================================
# نظام أزرار تيليغرام الاحترافي الشامل (بأسلوب Gemini Global Telegram Bot)
# ==============================================================================
def build_persistent_reply_kb():
    """لوحة الأزرار السفلية الدائمة لسهولة التحكم الفوري"""
    rk = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    rk.add(
        KeyboardButton("📺 فتح منصة البث الكاملة", web_app=WebAppInfo(url=WEBAPP_URL)),
        KeyboardButton("🔴 المباريات الجارية الآن")
    )
    rk.add(
        KeyboardButton("📅 جميع مباريات اليوم (كل الدوريات)"),
        KeyboardButton("📡 القنوات الرياضية الناقلة")
    )
    rk.add(
        KeyboardButton("🏆 تصفية حسب البطولة"),
        KeyboardButton("🛡️ إعدادات الإنترنت الضعيف")
    )
    return rk

def build_matches_inline_kb(matches, page=0, per_page=8, league="all"):
    """عرض جميع المباريات بلا استثناء مع أزرار التنقل بين الصفحات (Pagination)"""
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("📺 فتح المشغل الذكي والقنوات الناقلة (بدون تقطيع)", web_app=WebAppInfo(url=WEBAPP_URL)))

    total = len(matches)
    start = page * per_page
    end = start + per_page
    sliced = matches[start:end]

    for m in sliced:
        btn_text = f"{m['home']} ({m['score']}) {m['away']} | {m['status']} 📡 {m['broadcaster']}"
        kb.add(InlineKeyboardButton(btn_text[:64], web_app=WebAppInfo(url=WEBAPP_URL)))

    nav_btns = []
    if page > 0:
        nav_btns.append(InlineKeyboardButton("⬅️ الصفحة السابقة", callback_data=f"mpage_{league}_{page-1}"))
    if end < total:
        nav_btns.append(InlineKeyboardButton(f"الصفحة التالية ({end+1}-{min(end+per_page, total)} من {total}) ➡️", callback_data=f"mpage_{league}_{page+1}"))
    if nav_btns:
        kb.row(*nav_btns)

    kb.row(
        InlineKeyboardButton("🏆 اختيار دوري محدد", callback_data="menu_leagues"),
        InlineKeyboardButton("📡 قائمة القنوات", callback_data="menu_channels")
    )
    kb.add(InlineKeyboardButton("🔄 تحديث النتائج اللحظية الآن", callback_data=f"mpage_{league}_{page}"))
    return kb

def build_leagues_inline_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    btns = [InlineKeyboardButton(name, callback_data=f"mpage_{code}_0") for code, name in LEAGUES]
    kb.add(*btns)
    kb.add(InlineKeyboardButton("🔙 رجوع لكل المباريات", callback_data="mpage_all_0"))
    return kb

def build_channels_inline_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    for ch in VERIFIED_CHANNELS:
        kb.add(InlineKeyboardButton(ch["name"], web_app=WebAppInfo(url=WEBAPP_URL)))
    kb.add(InlineKeyboardButton("🔙 رجوع لجدول المباريات", callback_data="mpage_all_0"))
    return kb

if bot:
    @bot.message_handler(commands=["start", "help"])
    def cmd_start(msg):
        bot.send_message(
            msg.chat.id,
            "⚽ <b>أهلاً بك في PulseGoal Global Ultra (الإصدار الاحترافي الشامل)</b>\n\n"
            "✅ تم تفعيل <b>لوحة التحكم السفلية الدائمة</b> وجلب <b>جميع مباريات العالم والقنوات الناقلة</b> مع محرك البروكسي الذكي المضاد للتقطيع.",
            reply_markup=build_persistent_reply_kb()
        )
        matches = fetch_all_world_matches("all")
        bot.send_message(
            msg.chat.id,
            f"📡 <b>جدول المباريات العالمي الشامل ({len(matches)} مباراة مسجلة اليوم):</b>\n"
            "اضغط على أي مباراة لفتح القنوات الناقلة أو تصفح الصفحات بالأسفل:",
            reply_markup=build_matches_inline_kb(matches, page=0, league="all")
        )

    @bot.message_handler(func=lambda m: True)
    def handle_text_buttons(msg):
        txt = (msg.text or "").strip()
        if "المباريات الجارية" in txt:
            all_m = fetch_all_world_matches("all")
            live_m = [m for m in all_m if m["state"] == "in"] or all_m
            bot.send_message(
                msg.chat.id,
                f"🔴 <b>المباريات الجارية والقادمة ({len(live_m)} مباراة):</b>",
                reply_markup=build_matches_inline_kb(live_m, page=0, league="all")
            )
        elif "جميع مباريات اليوم" in txt:
            all_m = fetch_all_world_matches("all")
            bot.send_message(
                msg.chat.id,
                f"📅 <b>جميع مباريات اليوم في كافة البطولات ({len(all_m)} مباراة):</b>",
                reply_markup=build_matches_inline_kb(all_m, page=0, league="all")
            )
        elif "القنوات الرياضية" in txt:
            bot.send_message(
                msg.chat.id,
                "📺 <b>باقة القنوات الرياضية العربية والعالمية الناقلة (مدعومة بدرع البروكسي):</b>",
                reply_markup=build_channels_inline_kb()
            )
        elif "تصفية حسب البطولة" in txt:
            bot.send_message(
                msg.chat.id,
                "🏆 <b>اختر البطولة أو الدوري لعرض جميع مبارياته وقنواته الناقلة:</b>",
                reply_markup=build_leagues_inline_kb()
            )
        elif "الإنترنت الضعيف" in txt:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🛡️ فتح المشغل بوضع 240p + درع البروكسي", web_app=WebAppInfo(url=WEBAPP_URL)))
            bot.send_message(
                msg.chat.id,
                "🛡️ <b>نظام البث للإنترنت الضعيف (Low-Bandwidth Shield):</b>\n"
                "• يعمل البروكسي المدمج (`/proxy/stream`) على تمرير البث عبر خوادمنا لمنع التقطيع وتجاوز حظر المتصفح.\n"
                "• يمكنك التبديل الفوري داخل المشغل إلى دقة <b>240p</b> أو <b>وضع الراديو الصوتي (64kbps)</b>.",
                reply_markup=kb
            )
        else:
            cmd_start(msg)

    @bot.callback_query_handler(func=lambda call: True)
    def handle_inline_callbacks(call):
        data = call.data or ""
        if data.startswith("mpage_"):
            parts = data.split("_")
            league = parts[1]
            page = int(parts[2])
            matches = fetch_all_world_matches(league)
            bot.answer_callback_query(call.id, f"✅ تم جلب {len(matches)} مباراة")
            try:
                bot.edit_message_text(
                    f"📡 <b>جدول المباريات الشامل ({len(matches)} مباراة) — صفحة {page+1}:</b>\n"
                    "اضغط على أي مباراة لفتح المشغل والقنوات الناقلة:",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=build_matches_inline_kb(matches, page=page, league=league)
                )
            except Exception:
                pass
        elif data == "menu_leagues":
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                "🏆 <b>اختر البطولة لعرض جميع مبارياتها:</b>",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=build_leagues_inline_kb()
            )
        elif data == "menu_channels":
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                "📺 <b>القنوات الرياضية العربية والعالمية المباشرة:</b>",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=build_channels_inline_kb()
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
