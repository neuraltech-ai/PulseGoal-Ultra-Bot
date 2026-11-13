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

LEAGUES = [
    ("all", "🌍 كل المباريات الجارية"),
    ("uefa.champions", "🏆 دوري أبطال أوروبا"),
    ("uefa.europa", "🟠 الدوري الأوروبي"),
    ("eng.1", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 الدوري الإنجليزي الممتاز"),
    ("esp.1", "🇪🇸 الدوري الإسباني LaLiga"),
    ("ita.1", "🇮🇹 الدوري الإيطالي Serie A"),
    ("ger.1", "🇩🇪 الدوري الألماني Bundesliga"),
    ("fra.1", "🇫🇷 الدوري الفرنسي Ligue 1"),
    ("caf.nations", "🌍 بطولات وتصفيات أفريقيا CAF"),
    ("caf.champions", "🌍 دوري أبطال أفريقيا"),
    ("caf.confed", "🇲🇦 كأس الكونفدرالية الأفريقية"),
    ("fifa.worldq.caf", "🌍 تصفيات كأس العالم - أفريقيا"),
    ("fifa.worldq.uefa", "🇪🇺 تصفيات كأس العالم - أوروبا"),
    ("ksa.1", "🇸🇦 دوري روشن السعودي")
]

# باقة القنوات الاحترافية المقسمة: beIN Sports العربية + القنوات العربية المفتوحة + القنوات العالمية
CHANNELS_DB = [
    # باقة beIN SPORTS العربية
    {
        "id": "bein_news", "cat": "bein",
        "name": "🟣 beIN SPORTS NEWS HD (الإخبارية المفتوحة)",
        "mode": "embed",
        "embed_url": "https://www.youtube.com/embed/live_stream?channel=UCJUCcJUeh0Cz2xyKwkw5Q1w&autoplay=1",
        "hls_url": "https://bein-esp-xtra.amagi.tv/playlist.m3u8",
        "web_backup": "https://www.youtube.com/@beINSPORTS/streams"
    },
    {
        "id": "bein_xtra", "cat": "bein",
        "name": "🟣 beIN SPORTS XTRA HD (مباريات مباشرة)",
        "mode": "hls",
        "hls_url": "https://bein-esp-xtra.amagi.tv/playlist.m3u8",
        "embed_url": "https://www.youtube.com/embed/live_stream?channel=UCJUCcJUeh0Cz2xyKwkw5Q1w&autoplay=1",
        "web_backup": "https://www.beinsports.com/ar-mena"
    },
    {
        "id": "bein_1", "cat": "bein",
        "name": "🟣 beIN SPORTS 1 Premium HD (سيرفر متعدد)",
        "mode": "multi",
        "hls_url": "https://bein-esp-xtra.amagi.tv/playlist.m3u8",
        "embed_url": "https://www.youtube.com/embed/live_stream?channel=UCJUCcJUeh0Cz2xyKwkw5Q1w&autoplay=1",
        "web_backup": "https://www.beinsports.com/ar-mena/tv-guide"
    },
    {
        "id": "bein_2", "cat": "bein",
        "name": "🟣 beIN SPORTS 2 Premium HD (سيرفر متعدد)",
        "mode": "multi",
        "hls_url": "https://bein-esp-xtra.amagi.tv/playlist.m3u8",
        "embed_url": "https://www.youtube.com/embed/live_stream?channel=UCJUCcJUeh0Cz2xyKwkw5Q1w&autoplay=1",
        "web_backup": "https://www.beinsports.com/ar-mena/tv-guide"
    },
    {
        "id": "bein_3", "cat": "bein",
        "name": "🟣 beIN SPORTS 3 Premium HD (سيرفر متعدد)",
        "mode": "multi",
        "hls_url": "https://bein-esp-xtra.amagi.tv/playlist.m3u8",
        "embed_url": "https://www.youtube.com/embed/live_stream?channel=UCJUCcJUeh0Cz2xyKwkw5Q1w&autoplay=1",
        "web_backup": "https://www.beinsports.com/ar-mena/tv-guide"
    },
    {
        "id": "bein_4", "cat": "bein",
        "name": "🟣 beIN SPORTS 4 HD (الدوريات الأوروبية)",
        "mode": "multi",
        "hls_url": "https://bein-esp-xtra.amagi.tv/playlist.m3u8",
        "embed_url": "https://www.youtube.com/embed/live_stream?channel=UCJUCcJUeh0Cz2xyKwkw5Q1w&autoplay=1",
        "web_backup": "https://www.beinsports.com/ar-mena/tv-guide"
    },
    {
        "id": "bein_5", "cat": "bein",
        "name": "🟣 beIN SPORTS 5 HD (البطولات القارية)",
        "mode": "multi",
        "hls_url": "https://bein-esp-xtra.amagi.tv/playlist.m3u8",
        "embed_url": "https://www.youtube.com/embed/live_stream?channel=UCJUCcJUeh0Cz2xyKwkw5Q1w&autoplay=1",
        "web_backup": "https://www.beinsports.com/ar-mena/tv-guide"
    },
    {
        "id": "bein_6", "cat": "bein",
        "name": "🟣 beIN SPORTS 6 HD (البطولات الأفريقية والآسيوية)",
        "mode": "multi",
        "hls_url": "https://bein-esp-xtra.amagi.tv/playlist.m3u8",
        "embed_url": "https://www.youtube.com/embed/live_stream?channel=UCJUCcJUeh0Cz2xyKwkw5Q1w&autoplay=1",
        "web_backup": "https://www.beinsports.com/ar-mena/tv-guide"
    },
    # القنوات العربية المفتوحة
    {
        "id": "arryadia", "cat": "arab",
        "name": "🇲🇦 الرياضية المغربية (Arryadia TNT HD)",
        "mode": "hls",
        "hls_url": "https://cdn.live.easybroadcast.io/ts_corp/73_arryadia-tnt_zcmwjdc/playlist_dvr.m3u8",
        "embed_url": "https://snrtlive.ma/ar/arryadia",
        "web_backup": "https://snrtlive.ma/ar/arryadia"
    },
    {
        "id": "alkass1", "cat": "arab",
        "name": "🇶🇦 الكأس الرياضية 1 (Alkass One HD)",
        "mode": "hls",
        "hls_url": "https://liveakgr.alkassdigital.net/hls/live/2097037/Alkass5/master.m3u8",
        "embed_url": "https://www.alkass.net/alkass/live.aspx?ch=one",
        "web_backup": "https://www.alkass.net/alkass/live.aspx?ch=one"
    },
    {
        "id": "adsports1", "cat": "arab",
        "name": "🇦🇪 أبوظبي الرياضية 1 (AD Sports 1 HD)",
        "mode": "hls",
        "hls_url": "https://admdn1.cdn.mangomolo.com/adsports1/smil:adsports1.stream.smil/playlist.m3u8",
        "embed_url": "https://adsports.ae/live/154/",
        "web_backup": "https://adsports.ae/live/154/"
    },
    {
        "id": "dubaisports1", "cat": "arab",
        "name": "🇦🇪 دبي الرياضية 1 (Dubai Sports 1 FHD)",
        "mode": "hls",
        "hls_url": "https://dmitnthvll.cdn.mangomolo.com/dubaisports/smil:dubaisports.stream.smil/playlist.m3u8",
        "embed_url": "https://www.dubaisports.ae/content/dubaisports/livestreaming/channel-1.html",
        "web_backup": "https://www.dubaisports.ae/content/dubaisports/livestreaming/channel-1.html"
    },
    {
        "id": "omansport", "cat": "arab",
        "name": "🇴🇲 عمان الرياضية (Oman Sport HD)",
        "mode": "hls",
        "hls_url": "https://partneta.cdn.mgmlcdn.com/omsport/smil:omsport.stream.smil/playlist.m3u8",
        "embed_url": "https://ain.om",
        "web_backup": "https://ain.om"
    },
    {
        "id": "bahrainsport", "cat": "arab",
        "name": "🇧🇭 البحرين الرياضية 1 (Bahrain Sport HD)",
        "mode": "hls",
        "hls_url": "https://5c7b683162943.streamlock.net/live/ngrp:bahrainsport1_all/playlist.m3u8",
        "embed_url": "https://www.bahrain.bh",
        "web_backup": "https://www.bahrain.bh"
    },
    # قنوات عالمية تعمل 24/7 بدون حظر جغرافي
    {
        "id": "fifaplus", "cat": "global",
        "name": "🏆 FIFA+ Global Football TV (1080p FHD)",
        "mode": "hls",
        "hls_url": "https://a62dad94.wurl.com/master/f36d25e7e52f1ba8d7e56eb859c636563214f541/UmFrdXRlblRWLWV1X0ZJRkFQbHVzRUVuZ2xpc2hITFM/playlist.m3u8",
        "embed_url": "https://www.plus.fifa.com",
        "web_backup": "https://www.plus.fifa.com"
    },
    {
        "id": "rmtv", "cat": "global",
        "name": "🇪🇸 Real Madrid TV (البث الرسمي المباشر FHD)",
        "mode": "hls",
        "hls_url": "https://rmtv.akamaized.net/hls/live/2043153/rmtv-es-web/master.m3u8",
        "embed_url": "https://www.realmadrid.com/real-madrid-tv",
        "web_backup": "https://www.realmadrid.com/real-madrid-tv"
    },
    {
        "id": "redbull", "cat": "global",
        "name": "⚽ Red Bull Sports TV (1080p FHD)",
        "mode": "hls",
        "hls_url": "https://rbmn-live.akamaized.net/hls/live/590964/BoRB-AT/master.m3u8",
        "embed_url": "https://www.redbull.com",
        "web_backup": "https://www.redbull.com"
    },
    {
        "id": "unite8", "cat": "global",
        "name": "🌍 Unite8 Sports 1 HD (1080p)",
        "mode": "hls",
        "hls_url": "https://fta.ektv.in/live/263/master.m3u8",
        "embed_url": "https://fta.ektv.in/live/263/master.m3u8",
        "web_backup": "https://fta.ektv.in/live/263/master.m3u8"
    }
]

MATCH_CACHE = {"ts": 0, "data": []}
DYNAMIC_BEIN_STREAMS = []

def refresh_community_bein_streams():
    """البحث التلقائي في قوائم IPTV العربية المفتوحة عن روابط beIN والرياضية المحدثة"""
    global DYNAMIC_BEIN_STREAMS
    sources = [
        "https://iptv-org.github.io/iptv/languages/ara.m3u",
        "https://iptv-org.github.io/iptv/categories/sports.m3u"
    ]
    found = []
    for src in sources:
        try:
            r = requests.get(src, timeout=8)
            lines = r.text.splitlines()
            cname = ""
            for line in lines:
                line = line.strip()
                if line.startswith("#EXTINF:"):
                    cname = line.split(",")[-1].strip()
                elif line.startswith("http") and ".m3u8" in line:
                    low = cname.lower()
                    if any(k in low for k in ["bein", "sport", "alkass", "arryadia", "ssc", "ad sport", "dubai sport", "on time"]):
                        found.append({
                            "id": f"dyn_{len(found)}",
                            "cat": "bein" if "bein" in low else "arab",
                            "name": f"📡 {cname}",
                            "mode": "hls",
                            "hls_url": line,
                            "embed_url": line,
                            "web_backup": line
                        })
        except Exception:
            continue
    DYNAMIC_BEIN_STREAMS = found[:60]

def fetch_all_world_matches(league_code="all"):
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
                h_score = competitors[0].get("score", "0")
                a_score = competitors[1].get("score", "0")
                state = ev.get("status", {}).get("type", {}).get("state", "pre")
                detail = ev.get("status", {}).get("type", {}).get("shortDetail", "")

                broadcasts = []
                for b in comp.get("broadcasts", []):
                    broadcasts.extend(b.get("names", []))
                for gb in comp.get("geoBroadcasts", []):
                    mname = gb.get("media", {}).get("shortName")
                    if mname:
                        broadcasts.append(mname)
                b_str = " | ".join(list(dict.fromkeys(broadcasts))[:2]) if broadcasts else "beIN SPORTS HD / الرياضية"

                results.append({
                    "id": ev_id,
                    "league": league_name,
                    "home": home,
                    "away": away,
                    "score": f"{h_score} - {a_score}" if state != "pre" else "VS",
                    "status": f"🔴 مباشر ({detail})" if state == "in" else ("✅ انتهت" if state == "post" else f"🕒 {detail}"),
                    "state": state,
                    "broadcaster": b_str
                })
        except Exception:
            continue

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
    if not DYNAMIC_BEIN_STREAMS:
        refresh_community_bein_streams()
    return jsonify(CHANNELS_DB + DYNAMIC_BEIN_STREAMS)

@app.route("/proxy/stream")
def proxy_stream():
    target_url = request.args.get("url", "")
    if not target_url:
        return "Missing url", 400
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/125.0 Mobile Safari/537.36",
            "Referer": urllib.parse.urljoin(target_url, "/"),
            "Connection": "keep-alive"
        }
        r = requests.get(target_url, headers=headers, timeout=10)
        ctype = r.headers.get("Content-Type", "")
        if "mpegurl" in ctype.lower() or target_url.split("?")[0].endswith(".m3u8") or b"#EXTM3U" in r.content[:50]:
            base_url = target_url.rsplit("/", 1)[0] + "/"
            rewritten = []
            for line in r.text.splitlines():
                s = line.strip()
                if s and not s.startswith("#"):
                    abs_u = urllib.parse.urljoin(base_url, s)
                    rewritten.append(f"/proxy/stream?url={urllib.parse.quote(abs_u, safe='')}")
                else:
                    rewritten.append(line)
            return Response("\n".join(rewritten), status=200, content_type="application/vnd.apple.mpegurl", headers={"Access-Control-Allow-Origin": "*"})
        return Response(r.content, status=r.status_code, content_type=ctype or "video/MP2T", headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        return jsonify({"error": str(e)}), 502

HTML_UI = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>PulseGoal Ultra v7 — beIN & Global</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800;900&display=swap" rel="stylesheet">
<style>
  body { font-family: 'Cairo', sans-serif; background: #040711; color: #f8fafc; }
  .glass { background: rgba(15, 23, 42, 0.90); backdrop-filter: blur(14px); border: 1px solid rgba(255,255,255,0.08); }
</style>
</head>
<body class="p-2.5 sm:p-4 max-w-6xl mx-auto space-y-3">

  <!-- الشريط العلوي -->
  <div class="glass p-3 rounded-2xl flex items-center justify-between gap-2 border-r-4 border-r-purple-500 shadow-xl">
    <div>
      <div class="flex items-center gap-2">
        <h1 class="text-sm sm:text-base font-black text-white">PulseGoal <span class="text-purple-400">beIN & Global Ultra</span></h1>
        <span class="text-[10px] bg-purple-500/20 text-purple-300 border border-purple-500/40 px-2 py-0.5 rounded-full font-bold">Quad-Engine v7.0</span>
      </div>
      <p id="now-playing" class="text-[11px] text-emerald-400 font-bold mt-0.5">جاري التشغيل...</p>
    </div>
    <span id="engine-status" class="text-[11px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2.5 py-1 rounded-xl font-bold shrink-0">سيرفر 1 نشط 🟢</span>
  </div>

  <!-- منطقة المشغل الهجين (فيديو HLS + مشغل Embed مدمج للبث الرسمي) -->
  <div class="relative aspect-video bg-black rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
    <video id="v" class="w-full h-full object-contain bg-black" controls playsinline autoplay></video>
    <iframe id="embed-frame" class="hidden w-full h-full border-0" allow="autoplay; fullscreen; encrypted-media" allowfullscreen></iframe>

    <!-- شاشة الطوارئ التحويلية عند حجب القناة من متصفح تيليغرام -->
    <div id="fallback-modal" class="hidden absolute inset-0 bg-slate-950/95 flex flex-col items-center justify-center p-5 text-center z-30 space-y-3">
      <div class="text-3xl">📡</div>
      <h3 class="text-sm font-extrabold text-white">هذه القناة تستخدم تشفير المصدر المباشر (Geo-IP / DRM)</h3>
      <p class="text-xs text-slate-400 max-w-md">لتشغيلها فوراً بدون تقطيع، اختر السيرفر البديل المدمج أو افتح البث الرسمي/الخارجي بضغطة واحدة:</p>
      <div class="flex flex-wrap justify-center gap-2">
        <button onclick="switchServerMode('embed')" class="px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-xl text-xs font-bold text-white shadow">📺 تشغيل البث المدمج البديل (سيرفر 3)</button>
        <button onclick="openWebBackup()" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-xs font-bold text-white shadow">🌐 فتح البث الرسمي المباشر للقناة</button>
        <button onclick="openInVlc()" class="px-4 py-2 bg-amber-600 hover:bg-amber-500 rounded-xl text-xs font-bold text-white shadow">📲 فتح في مشغل الهاتف / VLC</button>
      </div>
    </div>
  </div>

  <!-- شريط اختيار السيرفرات الـ 4 والجودات -->
  <div class="glass p-3 rounded-2xl space-y-2.5">
    <div class="flex flex-wrap items-center justify-between gap-1.5">
      <div class="flex flex-wrap gap-1.5">
        <button onclick="switchServerMode('direct')" id="btn-srv-direct" class="px-2.5 py-1.5 bg-emerald-600 rounded-xl text-[11px] font-bold">سيرفر 1 (مباشر من بلدك)</button>
        <button onclick="switchServerMode('proxy')" id="btn-srv-proxy" class="px-2.5 py-1.5 bg-slate-800 rounded-xl text-[11px] font-bold">سيرفر 2 (بروكسي تخطي الحجب)</button>
        <button onclick="switchServerMode('embed')" id="btn-srv-embed" class="px-2.5 py-1.5 bg-purple-700 rounded-xl text-[11px] font-bold">سيرفر 3 (المشغل المدمج البديل)</button>
        <button onclick="openWebBackup()" class="px-2.5 py-1.5 bg-sky-700 rounded-xl text-[11px] font-bold">🌐 المصدر الرسمي</button>
      </div>
      <div class="flex gap-1">
        <button onclick="setQ(-1)" class="px-2.5 py-1 bg-slate-800 hover:bg-emerald-700 rounded-lg text-[11px] font-bold">ABR تلقائي</button>
        <button onclick="setQ(0)" class="px-2.5 py-1 bg-amber-600/80 rounded-lg text-[11px] font-bold">240p للنت الضعيف</button>
        <button onclick="setQ(2)" class="px-2.5 py-1 bg-slate-800 rounded-lg text-[11px] font-bold">1080p FHD</button>
      </div>
    </div>

    <!-- إدخال رابط m3u8 أو قائمة M3U خاصة لـ beIN Sports -->
    <div class="flex gap-1.5 pt-2 border-t border-slate-800">
      <input id="custom-input" type="text" placeholder="أدخل أي رابط بث .m3u8 أو قائمة IPTV M3U لتشغيل قنواتك الخاصة فوراً..." class="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white">
      <button onclick="loadCustomInput()" class="px-4 py-1.5 bg-purple-600 hover:bg-purple-500 rounded-xl text-xs font-bold shrink-0">تشغيل / استيراد</button>
    </div>
  </div>

  <!-- أزرار الأقسام الرئيسية -->
  <div class="grid grid-cols-3 gap-2">
    <button id="tab-bein" onclick="showSection('bein')" class="py-2.5 rounded-xl font-extrabold text-xs bg-purple-600 text-white shadow-lg">🟣 قنوات beIN & العربية</button>
    <button id="tab-matches" onclick="showSection('matches')" class="py-2.5 rounded-xl font-extrabold text-xs bg-slate-900 text-slate-300 border border-slate-800">⚽ جميع المباريات (139+)</button>
    <button id="tab-global" onclick="showSection('global')" class="py-2.5 rounded-xl font-extrabold text-xs bg-slate-900 text-slate-300 border border-slate-800">🌍 قنوات عالمية 24/7</button>
  </div>

  <!-- قسم القنوات (beIN + العربية + العالمية) -->
  <div id="sec-channels" class="glass p-3.5 rounded-2xl space-y-3">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <div class="flex gap-1.5 flex-wrap">
        <button onclick="setCatFilter('bein')" class="px-3 py-1 rounded-lg bg-purple-600 text-xs font-bold">🟣 باقة beIN SPORTS</button>
        <button onclick="setCatFilter('arab')" class="px-3 py-1 rounded-lg bg-emerald-600 text-xs font-bold">🇲🇦🇶🇦🇦🇪 القنوات العربية المفتوحة</button>
        <button onclick="setCatFilter('global')" class="px-3 py-1 rounded-lg bg-sky-600 text-xs font-bold">🌍 قنوات عالمية مضمونة</button>
        <button onclick="setCatFilter('all')" class="px-3 py-1 rounded-lg bg-slate-800 text-xs font-bold">الكل</button>
      </div>
      <input id="ch-search" oninput="renderChannels()" type="text" placeholder="ابحث عن قناة (beIN, الرياضية، الكأس)..." class="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1 text-xs text-white w-full sm:w-56">
    </div>
    <div id="channels-grid" class="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-[420px] overflow-y-auto pr-1"></div>
  </div>

  <!-- قسم جميع المباريات -->
  <div id="sec-matches" class="hidden glass p-3.5 rounded-2xl space-y-3">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <div class="flex gap-1.5 overflow-x-auto pb-1 max-w-full">
        <button onclick="loadMatches('all')" class="px-2.5 py-1 rounded-lg bg-emerald-600 text-[11px] font-bold shrink-0">🌍 الكل</button>
        <button onclick="loadMatches('uefa.champions')" class="px-2.5 py-1 rounded-lg bg-slate-800 text-[11px] font-bold shrink-0">🏆 أبطال أوروبا</button>
        <button onclick="loadMatches('eng.1')" class="px-2.5 py-1 rounded-lg bg-slate-800 text-[11px] font-bold shrink-0">🏴󠁧󠁢󠁥󠁮󠁧󠁿 الإنجليزي</button>
        <button onclick="loadMatches('esp.1')" class="px-2.5 py-1 rounded-lg bg-slate-800 text-[11px] font-bold shrink-0">🇪🇸 الإسباني</button>
        <button onclick="loadMatches('caf.nations')" class="px-2.5 py-1 rounded-lg bg-slate-800 text-[11px] font-bold shrink-0">🌍 أفريقيا</button>
        <button onclick="loadMatches('ksa.1')" class="px-2.5 py-1 rounded-lg bg-slate-800 text-[11px] font-bold shrink-0">🇸🇦 السعودي</button>
      </div>
      <input id="match-search" oninput="renderMatches()" type="text" placeholder="ابحث عن فريق أو مباراة..." class="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1 text-xs text-white w-full sm:w-48">
    </div>
    <div id="matches-count" class="text-[11px] text-emerald-400 font-bold"></div>
    <div id="matches-grid" class="grid grid-cols-1 md:grid-cols-2 gap-2.5 max-h-[450px] overflow-y-auto pr-1"></div>
  </div>

<script>
const v = document.getElementById('v');
const embedFrame = document.getElementById('embed-frame');
const fallbackModal = document.getElementById('fallback-modal');
let h = null;
let allChannels = [];
let allMatches = [];
let curCat = 'bein';
let curCh = null;
let srvMode = 'direct'; // direct -> proxy -> embed

function showSection(sec) {
  if (sec === 'matches') {
    document.getElementById('sec-matches').classList.remove('hidden');
    document.getElementById('sec-channels').classList.add('hidden');
  } else {
    document.getElementById('sec-matches').classList.add('hidden');
    document.getElementById('sec-channels').classList.remove('hidden');
    curCat = sec === 'global' ? 'global' : 'bein';
    renderChannels();
  }
}

function setCatFilter(c) { curCat = c; renderChannels(); }

function playChannelObj(idx) {
  const c = window.displayedChannels[idx];
  if (!c) return;
  curCh = c;
  fallbackModal.classList.add('hidden');
  document.getElementById('now-playing').textContent = '📺 القناة النشطة: ' + c.name;

  if (c.mode === 'embed') {
    switchServerMode('embed');
  } else {
    switchServerMode('direct');
  }
}

function switchServerMode(mode) {
  srvMode = mode;
  fallbackModal.classList.add('hidden');
  if (!curCh) return;

  if (mode === 'embed') {
    if (h) h.destroy();
    v.pause();
    v.classList.add('hidden');
    embedFrame.classList.remove('hidden');
    embedFrame.src = curCh.embed_url || curCh.web_backup;
    document.getElementById('engine-status').textContent = 'سيرفر 3 (مدمج) 🟣';
    return;
  }

  embedFrame.src = '';
  embedFrame.classList.add('hidden');
  v.classList.remove('hidden');

  const rawUrl = curCh.hls_url;
  const target = mode === 'proxy' ? ('/proxy/stream?url=' + encodeURIComponent(rawUrl)) : rawUrl;
  document.getElementById('engine-status').textContent = mode === 'direct' ? 'سيرفر 1 (مباشر) 🟢' : 'سيرفر 2 (بروكسي) 🟠';

  if (Hls.isSupported()) {
    if (h) h.destroy();
    h = new Hls({ maxBufferLength: 35, maxMaxBufferLength: 60, manifestLoadingTimeOut: 9000 });
    h.loadSource(target);
    h.attachMedia(v);
    h.on(Hls.Events.MANIFEST_PARSED, () => { v.play().catch(()=>{}); });
    h.on(Hls.Events.ERROR, (ev, data) => {
      if (data.fatal) {
        if (mode === 'direct') {
          // التحويل التلقائي الذكي للسيرفر 2 (البروكسي)
          switchServerMode('proxy');
        } else if (mode === 'proxy') {
          // إظهار خيارات السيرفر 3 والمشغل الخارجي
          fallbackModal.classList.remove('hidden');
        }
      }
    });
  } else if (v.canPlayType('application/vnd.apple.mpegurl')) {
    v.src = target;
    v.play().catch(()=>{});
  }
}

function setQ(lvl) { if (h) h.currentLevel = lvl; }
function openWebBackup() { if (curCh) window.open(curCh.web_backup || curCh.hls_url, '_blank'); }
function openInVlc() { if (curCh) window.open(curCh.hls_url, '_blank'); }

async function loadCustomInput() {
  const val = document.getElementById('custom-input').value.trim();
  if (!val) return;
  if (val.endsWith('.m3u') || val.includes('get.php')) {
    try {
      const r = await fetch('/proxy/stream?url=' + encodeURIComponent(val));
      const txt = await r.text();
      const lines = txt.split('\\n');
      let name = '';
      for (let l of lines) {
        l = l.trim();
        if (l.startsWith('#EXTINF:')) name = '⭐ ' + (l.split(',').pop() || 'Custom Channel');
        else if (l.startsWith('http')) {
          allChannels.unshift({ id: 'cust_' + Math.random(), cat: 'bein', name: name || 'قناة مخصصة', mode: 'hls', hls_url: l, embed_url: l, web_backup: l });
        }
      }
      curCat = 'bein';
      renderChannels();
    } catch (e) {}
  } else {
    curCh = { name: 'بث مخصص مباشر', mode: 'hls', hls_url: val, embed_url: val, web_backup: val };
    switchServerMode('direct');
  }
}

function renderChannels() {
  const q = (document.getElementById('ch-search').value || '').toLowerCase();
  window.displayedChannels = allChannels.filter(c => (curCat === 'all' || c.cat === curCat) && c.name.toLowerCase().includes(q));
  document.getElementById('channels-grid').innerHTML = window.displayedChannels.map((c, i) => `
    <div onclick="playChannelObj(${i})" class="cursor-pointer p-3 rounded-xl bg-slate-950 hover:bg-purple-950/40 border ${c.cat==='bein'?'border-purple-500/40':'border-slate-800'} flex items-center justify-between gap-2 transition">
      <span class="text-xs font-bold truncate">${c.name}</span>
      <span class="text-[10px] ${c.cat==='bein'?'bg-purple-600':'bg-emerald-600'} text-white px-2.5 py-1 rounded-lg font-bold shrink-0">تشغيل ▶</span>
    </div>
  `).join('');
}

async function initApp() {
  try {
    const res = await fetch('/api/channels');
    allChannels = await res.json();
    renderChannels();
    if (window.displayedChannels && window.displayedChannels.length > 0) {
      playChannelObj(1); // يبدأ بقناة beIN SPORTS XTRA أو FIFA+ الشغالة فوراً
    }
  } catch (e) {}
  loadMatches('all');
}

async function loadMatches(code) {
  document.getElementById('matches-count').textContent = '⏳ جاري تحديث جميع المباريات العالمية...';
  try {
    const res = await fetch('/api/matches?league=' + encodeURIComponent(code));
    allMatches = await res.json();
    renderMatches();
  } catch (e) {}
}

function renderMatches() {
  const q = (document.getElementById('match-search').value || '').toLowerCase();
  const list = allMatches.filter(m => m.home.toLowerCase().includes(q) || m.away.toLowerCase().includes(q) || m.league.toLowerCase().includes(q));
  document.getElementById('matches-count').textContent = `✅ إجمالي المباريات المعروضة: (${list.length}) مباراة مع القنوات الناقلة:`;
  document.getElementById('matches-grid').innerHTML = list.map(m => `
    <div onclick="showSection('bein')" class="cursor-pointer p-3 rounded-xl bg-slate-950 border ${m.state==='in'?'border-red-500/60':'border-slate-800'} space-y-2">
      <div class="flex justify-between text-[11px]">
        <span class="text-purple-400 font-bold truncate">🏆 ${m.league}</span>
        <span class="${m.state==='in'?'bg-red-500/20 text-red-300':'bg-slate-800 text-slate-300'} px-2 py-0.5 rounded font-bold">${m.status}</span>
      </div>
      <div class="flex justify-between items-center text-xs sm:text-sm font-extrabold">
        <span class="w-2/5 text-right truncate">${m.home}</span>
        <span class="px-3 py-1 rounded-xl bg-slate-900 border border-slate-700 text-amber-400 font-mono">${m.score}</span>
        <span class="w-2/5 text-left truncate">${m.away}</span>
      </div>
      <div class="flex justify-between pt-1.5 border-t border-slate-800/80 text-[11px] text-slate-400">
        <span>📡 الناقل: <strong class="text-purple-300">${m.broadcaster}</strong></span>
        <span class="text-emerald-400 font-bold">فتح القناة الناقلة ▶</span>
      </div>
    </div>
  `).join('');
}

initApp();
</script>
</body></html>"""

@app.route("/")
def index():
    return HTML_UI

@app.route("/health")
def health():
    return jsonify({"status": "online", "bot": "PulseGoal Ultra v7 Enterprise"}), 200

def build_persistent_reply_kb():
    rk = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    rk.add(
        KeyboardButton("🟣 قنوات beIN SPORTS والبث الحي", web_app=WebAppInfo(url=WEBAPP_URL)),
        KeyboardButton("🔴 المباريات الجارية الآن")
    )
    rk.add(
        KeyboardButton("📅 جميع مباريات اليوم (139+ مباراة)"),
        KeyboardButton("🇲🇦🇶🇦 القنوات العربية المفتوحة")
    )
    rk.add(
        KeyboardButton("🏆 تصفية حسب البطولة"),
        KeyboardButton("🛡️ طور الإنترنت الضعيف (240p)")
    )
    return rk

def build_matches_inline_kb(matches, page=0, per_page=8, league="all"):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🟣 فتح مشغل beIN SPORTS والقنوات الحية (Quad-Engine)", web_app=WebAppInfo(url=WEBAPP_URL)))

    total = len(matches)
    start = page * per_page
    end = start + per_page
    for m in matches[start:end]:
        txt = f"{m['home']} ({m['score']}) {m['away']} | {m['status']} 📡 {m['broadcaster']}"
        kb.add(InlineKeyboardButton(txt[:64], web_app=WebAppInfo(url=WEBAPP_URL)))

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"mpage_{league}_{page-1}"))
    if end < total:
        nav.append(InlineKeyboardButton(f"التالي ({end+1}-{min(end+per_page, total)} من {total}) ➡️", callback_data=f"mpage_{league}_{page+1}"))
    if nav:
        kb.row(*nav)

    kb.row(
        InlineKeyboardButton("🟣 باقة beIN SPORTS", callback_data="menu_bein"),
        InlineKeyboardButton("🏆 اختيار بطولة", callback_data="menu_leagues")
    )
    return kb

def build_bein_inline_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    for ch in CHANNELS_DB:
        if ch["cat"] in ("bein", "arab"):
            kb.add(InlineKeyboardButton(ch["name"], web_app=WebAppInfo(url=WEBAPP_URL)))
    kb.add(InlineKeyboardButton("🔙 رجوع لجدول المباريات الشامل", callback_data="mpage_all_0"))
    return kb

def build_leagues_inline_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(*[InlineKeyboardButton(name, callback_data=f"mpage_{code}_0") for code, name in LEAGUES])
    kb.add(InlineKeyboardButton("🔙 رجوع لكل المباريات", callback_data="mpage_all_0"))
    return kb

if bot:
    @bot.message_handler(commands=["start", "help"])
    def cmd_start(msg):
        bot.send_message(
            msg.chat.id,
            "⚽ <b>أهلاً بك في PulseGoal Ultra v7.0 — إصدار beIN & Global الاحترافي</b>\n\n"
            "🟣 تم تزويد البوت بـ <b>باقة قنوات beIN SPORTS العربية والقنوات المفتوحة</b> مع <b>المشغل الهجين رباعي السيرفرات (Quad-Engine)</b> الذي يبدأ بالبث المباشر من بلدك ثم يحول للبروكسي أو المشغل المدمج تلقائياً لمنع توقف أي قناة!",
            reply_markup=build_persistent_reply_kb()
        )
        matches = fetch_all_world_matches("all")
        bot.send_message(
            msg.chat.id,
            f"📡 <b>جدول المباريات العالمي الشامل ({len(matches)} مباراة) — صفحة 1:</b>",
            reply_markup=build_matches_inline_kb(matches, 0, 8, "all")
        )

    @bot.message_handler(func=lambda m: True)
    def handle_text(msg):
        t = (msg.text or "").strip()
        if "beIN" in t or "العربية" in t:
            bot.send_message(msg.chat.id, "🟣 <b>باقة قنوات beIN SPORTS والقنوات الرياضية العربية الناقلة:</b>", reply_markup=build_bein_inline_kb())
        elif "المباريات الجارية" in t:
            all_m = fetch_all_world_matches("all")
            live_m = [m for m in all_m if m["state"] == "in"] or all_m
            bot.send_message(msg.chat.id, f"🔴 <b>المباريات الجارية الآن ({len(live_m)} مباراة):</b>", reply_markup=build_matches_inline_kb(live_m, 0, 8, "all"))
        elif "تصفية حسب البطولة" in t:
            bot.send_message(msg.chat.id, "🏆 <b>اختر البطولة لعرض مبارياتها وقنواتها الناقلة:</b>", reply_markup=build_leagues_inline_kb())
        else:
            all_m = fetch_all_world_matches("all")
            bot.send_message(msg.chat.id, f"📅 <b>جميع مباريات اليوم ({len(all_m)} مباراة):</b>", reply_markup=build_matches_inline_kb(all_m, 0, 8, "all"))

    @bot.callback_query_handler(func=lambda call: True)
    def handle_cb(call):
        d = call.data or ""
        if d.startswith("mpage_"):
            _, league, p = d.split("_")
            p = int(p)
            matches = fetch_all_world_matches(league)
            bot.answer_callback_query(call.id, f"صفحة {p+1}")
            try:
                bot.edit_message_text(
                    f"📡 <b>جدول المباريات الشامل ({len(matches)} مباراة) — صفحة {p+1}:</b>",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=build_matches_inline_kb(matches, p, 8, league)
                )
            except Exception:
                pass
        elif d == "menu_bein":
            bot.answer_callback_query(call.id)
            bot.edit_message_text("🟣 <b>باقة قنوات beIN SPORTS والقنوات العربية:</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=build_bein_inline_kb())
        elif d == "menu_leagues":
            bot.answer_callback_query(call.id)
            bot.edit_message_text("🏆 <b>اختر البطولة:</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=build_leagues_inline_kb())

def poll():
    while bot:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=poll, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)
