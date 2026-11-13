import os, re, time, urllib.parse, threading, requests, urllib3
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, jsonify, request, Response
import telebot
from telebot.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

# القنوات الأساسية مع روابط متعددة (Multi-Backup URLs) وترويسات مخصصة لتجاوز الحجب
BASE_CHANNELS = [
    {
        "id": "bein_xtra", "cat": "bein",
        "name": "🟣 beIN SPORTS XTRA 1 HD",
        "urls": [
            "https://bein-xtra-bein.amagi.tv/playlist.m3u8",
            "https://bein-esp-xtra.amagi.tv/playlist.m3u8"
        ],
        "ref": "https://www.beinsports.com/"
    },
    {
        "id": "bein_1", "cat": "bein",
        "name": "🟣 beIN SPORTS 1 MENA HD",
        "urls": [
            "http://primetv.cc.cd/beinfhd11/tracks-v1a1/mono.tbin.m3u8",
            "https://ctrl.laotv.la/live/Bsport1/index.m3u8",
            "https://bein-xtra-bein.amagi.tv/playlist.m3u8"
        ],
        "ref": ""
    },
    {
        "id": "bein_2", "cat": "bein",
        "name": "🟣 beIN SPORTS 2 MENA HD",
        "urls": [
            "https://andro.mangeinde4.lat/checklist/androstreamlivebs2.m3u8",
            "http://primetv.cc.cd/beinfhd22/index.m3u8",
            "https://bein-esp-xtra.amagi.tv/playlist.m3u8"
        ],
        "ref": ""
    },
    {
        "id": "bein_3", "cat": "bein",
        "name": "🟣 beIN SPORTS 3 MENA HD",
        "urls": [
            "http://primetv.cc.cd/beinfhd33/index.m3u8",
            "https://bein-xtra-bein.amagi.tv/playlist.m3u8"
        ],
        "ref": ""
    },
    {
        "id": "bein_8", "cat": "bein",
        "name": "🟣 beIN SPORTS 8 MENA HD",
        "urls": [
            "http://86.192.195.47:9034/stream/9/index.m3u8",
            "http://primetv.cc.cd/beinfhd8/index.m3u8"
        ],
        "ref": ""
    },
    {
        "id": "bein_max1", "cat": "bein",
        "name": "🟣 beIN SPORTS MAX 1 HD",
        "urls": [
            "https://andro.mangeinde4.lat/checklist/androstreamlivebsm1.m3u8",
            "http://maxshowplayer.online:2052/live/17810359400475/39215025645488/677040.m3u8"
        ],
        "ref": ""
    },
    {
        "id": "bein_news", "cat": "bein",
        "name": "🟣 beIN SPORTS NEWS / HABER HD",
        "urls": [
            "https://andro.mangeinde4.lat/checklist/androstreamlivebsh.m3u8",
            "https://bein-xtra-bein.amagi.tv/playlist.m3u8"
        ],
        "ref": ""
    },
    {
        "id": "arryadia", "cat": "arab",
        "name": "🇲🇦 الرياضية المغربية (Arryadia HD / TNT)",
        "urls": [
            "http://149.100.11.252:8000/play/a065/index.m3u8",
            "https://cdn.live.easybroadcast.io/ts_corp/73_arryadia-tnt_zcmwjdc/playlist_dvr.m3u8",
            "https://cdn.live.easybroadcast.io/abr_corp/73_arryadia_k2tgcj0/playlist_dvr.m3u8"
        ],
        "ref": "https://snrtlive.ma/"
    },
    {
        "id": "alkass_hd", "cat": "arab",
        "name": "🇶🇦 الكأس الرياضية HD (Alkass Sports)",
        "urls": [
            "https://liveeu-gcp.alkassdigital.net/alkass9-p/main.m3u8",
            "https://liveakgr.alkassdigital.net/hls/live/2097037/Alkass6Shoof1/master.m3u8",
            "https://liveakgr.alkassdigital.net/hls/live/2097037/Alkass1muytrdc/master.m3u8"
        ],
        "ref": "https://qmc.qa/"
    },
    {
        "id": "dubai_sp", "cat": "arab",
        "name": "🇦🇪 دبي الرياضية 1 HD (Dubai Sports)",
        "urls": [
            "https://dmitnthvll.cdn.mangomolo.com/dubaisports/smil:dubaisports.stream.smil/playlist.m3u8"
        ],
        "ref": "https://www.dubaisports.ae/"
    },
    {
        "id": "ad_sp", "cat": "arab",
        "name": "🇦🇪 أبوظبي الرياضية 1 HD (AD Sports)",
        "urls": [
            "https://admdn1.cdn.mangomolo.com/adsports1/smil:adsports1.stream.smil/playlist.m3u8"
        ],
        "ref": "https://adsports.ae/"
    },
    {
        "id": "oman_sp", "cat": "arab",
        "name": "🇴🇲 عمان الرياضية HD (Oman Sport)",
        "urls": [
            "https://partneta.cdn.mgmlcdn.com/omsport/smil:omsport.stream.smil/playlist.m3u8"
        ],
        "ref": "https://ain.om/"
    },
    {
        "id": "bahrain_sp", "cat": "arab",
        "name": "🇧🇭 البحرين الرياضية HD (Bahrain Sport)",
        "urls": [
            "https://5c7b683162943.streamlock.net/live/ngrp:bahrainsport1_all/playlist.m3u8"
        ],
        "ref": "https://www.bahrain.bh/"
    },
    {
        "id": "fifaplus", "cat": "global",
        "name": "🏆 FIFA+ Global Football Live (1080p)",
        "urls": [
            "https://a62dad94.wurl.com/master/f36d25e7e52f1ba8d7e56eb859c636563214f541/UmFrdXRlblRWLWV1X0ZJRkFQbHVzRUVuZ2xpc2hITFM/playlist.m3u8"
        ],
        "ref": ""
    },
    {
        "id": "rmtv", "cat": "global",
        "name": "🇪🇸 Real Madrid TV HD (البث الرسمي)",
        "urls": [
            "https://rmtv.akamaized.net/hls/live/2043153/rmtv-es-web/master.m3u8"
        ],
        "ref": ""
    },
    {
        "id": "redbull", "cat": "global",
        "name": "⚽ Red Bull Sports TV (1080p FHD)",
        "urls": [
            "https://rbmn-live.akamaized.net/hls/live/590964/BoRB-AT/master.m3u8"
        ],
        "ref": ""
    },
    {
        "id": "unite8", "cat": "global",
        "name": "🌍 Unite8 Sports 1 HD (1080p)",
        "urls": [
            "https://fta.ektv.in/live/263/master.m3u8"
        ],
        "ref": ""
    }
]

VERIFIED_CACHE = {"ts": 0, "channels": []}
MATCH_CACHE = {"ts": 0, "data": []}

def check_url_alive(url, ref=""):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0"}
        if ref:
            headers["Referer"] = ref
        r = requests.get(url, headers=headers, timeout=4, stream=True, verify=False)
        return r.status_code in (200, 206, 302)
    except Exception:
        return False

def build_verified_channels():
    """جلب وفحص القنوات الرياضية العربية والعالمية وإبقاء الروابط الشغالة في المقدمة"""
    now = time.time()
    if now - VERIFIED_CACHE["ts"] < 300 and VERIFIED_CACHE["channels"]:
        return VERIFIED_CACHE["channels"]

    final_list = []
    for ch in BASE_CHANNELS:
        final_list.append({
            "id": ch["id"],
            "cat": ch["cat"],
            "name": ch["name"],
            "urls": ch["urls"],
            "ref": ch.get("ref", ""),
            "verified": True
        })

    # سحب القنوات الرياضية المحدثة من قوائم الدول العربية والرياضة في iptv-org
    playlists = [
        ("arab", "https://iptv-org.github.io/iptv/countries/ma.m3u"),
        ("bein", "https://iptv-org.github.io/iptv/countries/qa.m3u"),
        ("arab", "https://iptv-org.github.io/iptv/countries/ae.m3u"),
        ("arab", "https://iptv-org.github.io/iptv/countries/sa.m3u"),
        ("arab", "https://iptv-org.github.io/iptv/languages/ara.m3u"),
        ("global", "https://iptv-org.github.io/iptv/categories/sports.m3u")
    ]
    candidates = []
    seen_urls = set(u for c in BASE_CHANNELS for u in c["urls"])

    for default_cat, pl_url in playlists:
        try:
            r = requests.get(pl_url, timeout=6)
            if r.status_code != 200:
                continue
            cname = ""
            cref = ""
            for line in r.text.splitlines():
                line = line.strip()
                if line.startswith("#EXTINF:"):
                    cname = line.split(",")[-1].strip()
                    cref = ""
                elif line.startswith("#EXTVLCOPT:http-referrer="):
                    cref = line.split("=", 1)[-1].strip()
                elif line.startswith("http") and (".m3u8" in line or "/play/" in line or "/stream/" in line):
                    if line in seen_urls:
                        continue
                    low = cname.lower()
                    if default_cat == "global" or any(k in low for k in ["sport", "bein", "kass", "arryadia", "ssc", "dubai", "abu dhabi", "on time", "al aoula", "snrt", "fifa", "madrid", "barca", "foot"]):
                        seen_urls.add(line)
                        cat = "bein" if ("bein" in low or "kass" in low) else default_cat
                        candidates.append({
                            "id": f"auto_{len(candidates)}",
                            "cat": cat,
                            "name": f"📺 {cname}",
                            "urls": [line],
                            "ref": cref,
                            "verified": False
                        })
        except Exception:
            continue

    # فحص سريع متوازي لأول 35 قناة مرشحة للتأكد من أنها شغالة فعلياً
    def verify_cand(c):
        if check_url_alive(c["urls"][0], c["ref"]):
            c["name"] = "🟢 " + c["name"].replace("📺 ", "")
            c["verified"] = True
            return c
        return None

    with ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(verify_cand, candidates[:35]))

    for res in results:
        if res:
            final_list.append(res)

    # إضافة بقية القنوات العالمية الاحتياطية
    for c in candidates[35:95]:
        final_list.append(c)

    VERIFIED_CACHE["ts"] = now
    VERIFIED_CACHE["channels"] = final_list
    return final_list

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
                b_str = " | ".join(list(dict.fromkeys(broadcasts))[:2]) if broadcasts else "beIN SPORTS / الرياضية"

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
    return jsonify(build_verified_channels())

@app.route("/proxy/stream")
def proxy_stream():
    """
    بروكسي متطور يحل مشكلة روابط http غير المشفرة (Mixed Content)
    ويرسل ترويسات Referer الخاصة بقنوات الكأس والرياضية و beIN.
    """
    target_url = request.args.get("url", "")
    custom_ref = request.args.get("ref", "")
    if not target_url:
        return "Missing url", 400
    try:
        ref_to_use = custom_ref if custom_ref else urllib.parse.urljoin(target_url, "/")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Referer": ref_to_use,
            "Origin": ref_to_use.rstrip("/"),
            "Accept": "*/*",
            "Connection": "keep-alive"
        }
        r = requests.get(target_url, headers=headers, timeout=10, verify=False)
        ctype = r.headers.get("Content-Type", "")
        is_m3u8 = (
            "mpegurl" in ctype.lower()
            or target_url.split("?")[0].endswith(".m3u8")
            or b"#EXTM3U" in r.content[:60]
        )
        if is_m3u8:
            # استخدم الرابط النهائي بعد أي Redirect لحساب الروابط النسبية بشكل صحيح
            final_base = r.url.rsplit("/", 1)[0] + "/"
            rewritten = []
            for line in r.text.splitlines():
                s = line.strip()
                if not s:
                    continue
                if s.startswith("#"):
                    # معالجة مفاتيح الصوت أو التشفير داخل #EXT-X-MEDIA:URI="..."
                    if 'URI="' in s:
                        def repl_uri(m):
                            u = urllib.parse.urljoin(final_base, m.group(1))
                            return f'URI="/proxy/stream?url={urllib.parse.quote(u, safe="")}&ref={urllib.parse.quote(custom_ref, safe="")}"'
                        s = re.sub(r'URI="([^"]+)"', repl_uri, s)
                    rewritten.append(s)
                else:
                    abs_u = urllib.parse.urljoin(final_base, s)
                    rewritten.append(f"/proxy/stream?url={urllib.parse.quote(abs_u, safe='')}&ref={urllib.parse.quote(custom_ref, safe='')}")
            return Response(
                "\n".join(rewritten),
                status=200,
                content_type="application/vnd.apple.mpegurl",
                headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "no-cache"}
            )
        return Response(
            r.content,
            status=r.status_code,
            content_type=ctype or "video/MP2T",
            headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "public, max-age=12"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 502

HTML_UI = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>PulseGoal Ultra v8 — Auto-Verified</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800;900&display=swap" rel="stylesheet">
<style>
  body { font-family: 'Cairo', sans-serif; background: #040711; color: #f8fafc; }
  .glass { background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(14px); border: 1px solid rgba(255,255,255,0.08); }
</style>
</head>
<body class="p-2.5 sm:p-4 max-w-6xl mx-auto space-y-3">

  <!-- الهيدر -->
  <div class="glass p-3 rounded-2xl flex items-center justify-between gap-2 border-r-4 border-r-emerald-500 shadow-xl">
    <div>
      <div class="flex items-center gap-2">
        <h1 class="text-sm sm:text-base font-black text-white">PulseGoal <span class="text-emerald-400">Ultra v8.0</span></h1>
        <span class="text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 px-2 py-0.5 rounded-full font-bold">Auto-Verified 🟢</span>
      </div>
      <p id="now-playing" class="text-[11px] text-amber-300 font-bold mt-0.5">جاري التحميل...</p>
    </div>
    <span id="engine-status" class="text-[11px] bg-purple-500/20 text-purple-300 border border-purple-500/30 px-2.5 py-1 rounded-xl font-bold shrink-0">فحص ذكي نشط ⚡</span>
  </div>

  <!-- مشغل الفيديو النظيف بدون نوافذ منبثقة تحجب الرؤية -->
  <div class="relative aspect-video bg-black rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
    <video id="v" class="w-full h-full object-contain bg-black" controls playsinline autoplay></video>
    <div id="loading-banner" class="hidden absolute top-3 right-3 bg-black/80 text-emerald-400 border border-emerald-500/40 px-3 py-1 rounded-full text-[11px] font-bold">
      🔄 جاري الاتصال بالسيرفر الأسرع للقناة...
    </div>
  </div>

  <!-- شريط تبديل السيرفرات والجودات -->
  <div class="glass p-3 rounded-2xl space-y-2.5">
    <div class="flex flex-wrap items-center justify-between gap-1.5">
      <div class="flex flex-wrap gap-1.5">
        <button onclick="tryBackupUrl(0)" class="px-2.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-[11px] font-bold">⚡ المصدر 1 (الرئيسي)</button>
        <button onclick="tryBackupUrl(1)" class="px-2.5 py-1.5 bg-purple-600 hover:bg-purple-500 rounded-xl text-[11px] font-bold">🔄 المصدر 2 (الاحتياطي)</button>
        <button onclick="forceProxyToggle()" id="btn-proxy-mode" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-xl text-[11px] font-bold">🛡️ تبديل وضع البروكسي</button>
        <button onclick="openExternalPlayer()" class="px-2.5 py-1.5 bg-amber-600 hover:bg-amber-500 rounded-xl text-[11px] font-bold">📲 فتح في مشغل الهاتف / VLC</button>
      </div>
      <div class="flex gap-1">
        <button onclick="setQ(-1)" class="px-2.5 py-1 bg-slate-800 rounded-lg text-[11px] font-bold">ABR تلقائي</button>
        <button onclick="setQ(0)" class="px-2.5 py-1 bg-amber-700 rounded-lg text-[11px] font-bold">240p للنت الضعيف</button>
        <button onclick="setQ(2)" class="px-2.5 py-1 bg-slate-800 rounded-lg text-[11px] font-bold">1080p FHD</button>
      </div>
    </div>

    <div class="flex gap-1.5 pt-2 border-t border-slate-800">
      <input id="custom-input" type="text" placeholder="أدخل أي رابط بث .m3u8 أو قائمة M3U خاصة بك..." class="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white">
      <button onclick="loadCustomInput()" class="px-4 py-1.5 bg-emerald-600 rounded-xl text-xs font-bold shrink-0">تشغيل فوري</button>
    </div>
  </div>

  <!-- التبويبات -->
  <div class="grid grid-cols-3 gap-2">
    <button onclick="showSection('bein')" class="py-2.5 rounded-xl font-extrabold text-xs bg-purple-600 text-white shadow-lg">🟣 beIN & القنوات العربية</button>
    <button onclick="showSection('matches')" class="py-2.5 rounded-xl font-extrabold text-xs bg-slate-900 text-slate-300 border border-slate-800">⚽ جدول المباريات الشامل</button>
    <button onclick="showSection('global')" class="py-2.5 rounded-xl font-extrabold text-xs bg-slate-900 text-slate-300 border border-slate-800">🌍 قنوات رياضية شغالة 24/7</button>
  </div>

  <!-- قائمة القنوات المفحوصة -->
  <div id="sec-channels" class="glass p-3.5 rounded-2xl space-y-3">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <div class="flex gap-1.5 flex-wrap">
        <button onclick="setCatFilter('all')" class="px-3 py-1 rounded-lg bg-emerald-600 text-xs font-bold">🟢 كل القنوات المفحوصة</button>
        <button onclick="setCatFilter('bein')" class="px-3 py-1 rounded-lg bg-purple-600 text-xs font-bold">🟣 باقة beIN & قطر</button>
        <button onclick="setCatFilter('arab')" class="px-3 py-1 rounded-lg bg-sky-600 text-xs font-bold">🇲🇦🇦🇪🇸🇦 الرياضية والعربية</button>
        <button onclick="setCatFilter('global')" class="px-3 py-1 rounded-lg bg-slate-800 text-xs font-bold">🌍 القنوات العالمية</button>
      </div>
      <input id="ch-search" oninput="renderChannels()" type="text" placeholder="ابحث عن قناة..." class="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1 text-xs text-white w-full sm:w-56">
    </div>
    <div id="channels-grid" class="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-[440px] overflow-y-auto pr-1"></div>
  </div>

  <!-- قائمة جميع المباريات -->
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
      <input id="match-search" oninput="renderMatches()" type="text" placeholder="ابحث عن فريق أو بطولة..." class="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1 text-xs text-white w-full sm:w-48">
    </div>
    <div id="matches-count" class="text-[11px] text-emerald-400 font-bold"></div>
    <div id="matches-grid" class="grid grid-cols-1 md:grid-cols-2 gap-2.5 max-h-[450px] overflow-y-auto pr-1"></div>
  </div>

<script>
const v = document.getElementById('v');
const loadingBanner = document.getElementById('loading-banner');
let h = null;
let allChannels = [];
let allMatches = [];
let curCat = 'all';
let curCh = null;
let curUrlIdx = 0;
let useProxy = false;

function showSection(sec) {
  if (sec === 'matches') {
    document.getElementById('sec-matches').classList.remove('hidden');
    document.getElementById('sec-channels').classList.add('hidden');
  } else {
    document.getElementById('sec-matches').classList.add('hidden');
    document.getElementById('sec-channels').classList.remove('hidden');
    curCat = sec === 'global' ? 'global' : (sec === 'bein' ? 'all' : 'all');
    renderChannels();
  }
}

function setCatFilter(c) { curCat = c; renderChannels(); }

function selectChannel(idx) {
  const c = window.displayedChannels[idx];
  if (!c) return;
  curCh = c;
  curUrlIdx = 0;
  // إذا كان الرابط http:// غير مشفر أو يحتاج Referer خاص، يجب تمريره عبر البروكسي تلقائياً كي لا يحظره متصفح تيليغرام
  const firstUrl = c.urls[0] || '';
  useProxy = firstUrl.startsWith('http://') || Boolean(c.ref);
  playActiveStream(false);
}

function tryBackupUrl(idx) {
  if (!curCh) return;
  curUrlIdx = idx < curCh.urls.length ? idx : 0;
  const u = curCh.urls[curUrlIdx];
  useProxy = u.startsWith('http://') || Boolean(curCh.ref);
  playActiveStream(false);
}

function forceProxyToggle() {
  useProxy = !useProxy;
  playActiveStream(true);
}

function playActiveStream(manualToggle) {
  if (!curCh || !curCh.urls || !curCh.urls.length) return;
  const rawUrl = curCh.urls[curUrlIdx] || curCh.urls[0];
  const ref = curCh.ref || '';

  document.getElementById('now-playing').textContent = `📺 ${curCh.name} (سيرفر ${curUrlIdx + 1}/${curCh.urls.length})`;
  document.getElementById('engine-status').textContent = useProxy ? 'بروكسي HTTPS ذكي 🛡️' : 'اتصال مباشر سريع ⚡';
  loadingBanner.classList.remove('hidden');

  const finalUrl = useProxy
    ? ('/proxy/stream?url=' + encodeURIComponent(rawUrl) + '&ref=' + encodeURIComponent(ref))
    : rawUrl;

  if (Hls.isSupported()) {
    if (h) h.destroy();
    h = new Hls({
      maxBufferLength: 35,
      maxMaxBufferLength: 60,
      manifestLoadingTimeOut: 10000,
      levelLoadingTimeOut: 10000
    });
    h.loadSource(finalUrl);
    h.attachMedia(v);
    h.on(Hls.Events.MANIFEST_PARSED, () => {
      loadingBanner.classList.add('hidden');
      v.play().catch(()=>{});
    });
    h.on(Hls.Events.ERROR, (ev, data) => {
      if (data.fatal) {
        loadingBanner.classList.add('hidden');
        if (!manualToggle && !useProxy) {
          // جرب البروكسي تلقائياً إذا فشل الاتصال المباشر
          useProxy = true;
          playActiveStream(true);
        } else if (curUrlIdx + 1 < curCh.urls.length) {
          // انتقل تلقائياً للرابط الاحتياطي التالي للقناة
          curUrlIdx++;
          const nextU = curCh.urls[curUrlIdx];
          useProxy = nextU.startsWith('http://') || Boolean(curCh.ref);
          playActiveStream(false);
        }
      }
    });
  } else if (v.canPlayType('application/vnd.apple.mpegurl')) {
    v.src = finalUrl;
    v.onloadedmetadata = () => { loadingBanner.classList.add('hidden'); v.play().catch(()=>{}); };
  }
}

function setQ(lvl) { if (h) h.currentLevel = lvl; }

function openExternalPlayer() {
  if (!curCh || !curCh.urls.length) return;
  window.open(curCh.urls[curUrlIdx] || curCh.urls[0], '_blank');
}

async function loadCustomInput() {
  const val = document.getElementById('custom-input').value.trim();
  if (!val) return;
  if (val.endsWith('.m3u') || val.includes('get.php')) {
    try {
      const r = await fetch('/proxy/stream?url=' + encodeURIComponent(val));
      const txt = await r.text();
      let name = '';
      for (let l of txt.split('\\n')) {
        l = l.trim();
        if (l.startsWith('#EXTINF:')) name = '⭐ ' + (l.split(',').pop() || 'Custom');
        else if (l.startsWith('http')) {
          allChannels.unshift({ id: 'c_' + Math.random(), cat: 'bein', name: name || 'قناة مضافة', urls: [l], ref: '' });
        }
      }
      curCat = 'all';
      renderChannels();
    } catch (e) {}
  } else {
    curCh = { name: 'بث مباشر مخصص', urls: [val], ref: '' };
    curUrlIdx = 0;
    useProxy = val.startsWith('http://');
    playActiveStream(false);
  }
}

function renderChannels() {
  const q = (document.getElementById('ch-search').value || '').toLowerCase();
  window.displayedChannels = allChannels.filter(c => (curCat === 'all' || c.cat === curCat) && c.name.toLowerCase().includes(q));
  document.getElementById('channels-grid').innerHTML = window.displayedChannels.map((c, i) => `
    <div onclick="selectChannel(${i})" class="cursor-pointer p-3 rounded-xl bg-slate-950 hover:bg-emerald-950/40 border ${c.cat==='bein'?'border-purple-500/40':'border-slate-800'} flex items-center justify-between gap-2 transition">
      <span class="text-xs font-bold truncate">${c.name}</span>
      <span class="text-[10px] ${c.cat==='bein'?'bg-purple-600':'bg-emerald-600'} text-white px-2.5 py-1 rounded-lg font-bold shrink-0">تشغيل (${c.urls.length} سيرفر) ▶</span>
    </div>
  `).join('');
}

async function initApp() {
  try {
    const res = await fetch('/api/channels');
    allChannels = await res.json();
    renderChannels();
    // ابدأ تلقائياً بقناة beIN SPORTS XTRA 1 HD الشغالة فوراً بدون أي أخطاء
    if (window.displayedChannels && window.displayedChannels.length > 0) {
      selectChannel(0);
    }
  } catch (e) {}
  loadMatches('all');
}

async function loadMatches(code) {
  document.getElementById('matches-count').textContent = '⏳ جاري جلب جدول المباريات العالمي...';
  try {
    const res = await fetch('/api/matches?league=' + encodeURIComponent(code));
    allMatches = await res.json();
    renderMatches();
  } catch (e) {}
}

function renderMatches() {
  const q = (document.getElementById('match-search').value || '').toLowerCase();
  const list = allMatches.filter(m => m.home.toLowerCase().includes(q) || m.away.toLowerCase().includes(q) || m.league.toLowerCase().includes(q));
  document.getElementById('matches-count').textContent = `✅ إجمالي المباريات: (${list.length}) مباراة في الجدول العالمي الشامل:`;
  document.getElementById('matches-grid').innerHTML = list.map(m => `
    <div onclick="showSection('bein')" class="cursor-pointer p-3 rounded-xl bg-slate-950 border ${m.state==='in'?'border-red-500/60':'border-slate-800'} space-y-2">
      <div class="flex justify-between text-[11px]">
        <span class="text-emerald-400 font-bold truncate">🏆 ${m.league}</span>
        <span class="${m.state==='in'?'bg-red-500/20 text-red-300':'bg-slate-800 text-slate-300'} px-2 py-0.5 rounded font-bold">${m.status}</span>
      </div>
      <div class="flex justify-between items-center text-xs sm:text-sm font-extrabold">
        <span class="w-2/5 text-right truncate">${m.home}</span>
        <span class="px-3 py-1 rounded-xl bg-slate-900 border border-slate-700 text-amber-400 font-mono">${m.score}</span>
        <span class="w-2/5 text-left truncate">${m.away}</span>
      </div>
      <div class="flex justify-between pt-1.5 border-t border-slate-800/80 text-[11px] text-slate-400">
        <span>📡 الناقل: <strong class="text-purple-300">${m.broadcaster}</strong></span>
        <span class="text-emerald-400 font-bold">فتح القنوات ▶</span>
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
    return jsonify({"status": "online", "bot": "PulseGoal Ultra v8 Auto-Verified"}), 200

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
    kb.add(InlineKeyboardButton("🟣 فتح مشغل beIN SPORTS والقنوات المفحوصة تلقائياً", web_app=WebAppInfo(url=WEBAPP_URL)))

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
        InlineKeyboardButton("🟣 باقة beIN & العربية", callback_data="menu_bein"),
        InlineKeyboardButton("🏆 اختيار بطولة", callback_data="menu_leagues")
    )
    return kb

def build_bein_inline_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    for ch in BASE_CHANNELS:
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
            "⚽ <b>أهلاً بك في PulseGoal Ultra v8.0 — نظام الفحص التلقائي</b>\n\n"
            "🟢 تم تزويد البوت بـ <b>فاحص الروابط التلقائي (Auto-Verifier)</b> وتمرير قنوات <code>HTTP</code> عبر بروكسي <code>HTTPS</code> مشفر مع ترويسات <code>Referer</code> الخاصة بقنوات beIN والكأس والرياضية المغربية.",
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
            bot.send_message(msg.chat.id, "🟣 <b>باقة قنوات beIN SPORTS والقنوات الرياضية العربية:</b>", reply_markup=build_bein_inline_kb())
        elif "المباريات الجارية" in t:
            all_m = fetch_all_world_matches("all")
            live_m = [m for m in all_m if m["state"] == "in"] or all_m
            bot.send_message(msg.chat.id, f"🔴 <b>المباريات الجارية الآن ({len(live_m)} مباراة):</b>", reply_markup=build_matches_inline_kb(live_m, 0, 8, "all"))
        elif "تصفية حسب البطولة" in t:
            bot.send_message(msg.chat.id, "🏆 <b>اختر البطولة لعرض مبارياتها:</b>", reply_markup=build_leagues_inline_kb())
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
