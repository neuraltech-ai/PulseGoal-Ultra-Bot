import os, re, time, datetime, urllib.parse, threading, requests, urllib3
from flask import Flask, jsonify, request, Response, stream_with_context
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

# قائمة البطولات الشاملة مع دوري الأمم الأوروبية وكأس أمم أوروبا وتصفياتها
LEAGUES = [
    ("all", "🔥 كل مباريات اليوم"),
    ("uefa.nations", "🇪🇺 دوري الأمم الأوروبية (Nations League)"),
    ("uefa.euro", "🏆 كأس أمم أوروبا (UEFA EURO)"),
    ("uefa.euroq", "🇪🇺 تصفيات كأس أمم أوروبا"),
    ("uefa.champions", "⚽ دوري أبطال أوروبا"),
    ("uefa.europa", "🟠 الدوري الأوروبي"),
    ("eng.1", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 الدوري الإنجليزي الممتاز"),
    ("esp.1", "🇪🇸 الدوري الإسباني LaLiga"),
    ("ita.1", "🇮🇹 الدوري الإيطالي Serie A"),
    ("ger.1", "🇩🇪 الدوري الألماني Bundesliga"),
    ("fra.1", "🇫🇷 الدوري الفرنسي Ligue 1"),
    ("caf.nations", "🌍 كأس أمم أفريقيا وتصفياتها"),
    ("caf.champions", "🌍 دوري أبطال أفريقيا"),
    ("caf.confed", "🇲🇦 كأس الكونفدرالية الأفريقية"),
    ("fifa.worldq.caf", "🌍 تصفيات كأس العالم - أفريقيا"),
    ("fifa.worldq.uefa", "🇪🇺 تصفيات كأس العالم - أوروبا"),
    ("fifa.friendly", "🌐 المباريات الدولية الودية"),
    ("ksa.1", "🇸🇦 دوري روشن السعودي")
]

# باقات القنوات المصممة بأسلوب Yacine TV & Drama Live (متعددة السيرفرات والجودات)
YACINE_BOUQUETS = [
    # باقة beIN SPORTS المفتوحة والبديلة بجميع الجودات
    {
        "id": "bein_news", "bouquet": "bein_fhd",
        "name": "beIN SPORTS NEWS HD (الإخبارية)",
        "badge": "1080p FHD", "logo": "🟣",
        "servers": [
            {"label": "سيرفر 1 (FHD)", "url": "https://live.kwikmotion.com/beinsportsnewslive/beinsportsnews.smil/playlist.m3u8", "ref": "https://beinsports.com/ar/", "proxy": True},
            {"label": "سيرفر 2 (HD)", "url": "https://andro.mangeinde4.lat/checklist/androstreamlivebsh.m3u8", "ref": "", "proxy": False},
            {"label": "سيرفر 3 (SD)", "url": "https://bein-xtra-bein.amagi.tv/playlist.m3u8", "ref": "", "proxy": False}
        ]
    },
    {
        "id": "bein_xtra1", "bouquet": "bein_fhd",
        "name": "beIN SPORTS XTRA 1 Premium",
        "badge": "1080p FHD", "logo": "🟣",
        "servers": [
            {"label": "سيرفر 1 (1080p)", "url": "https://bein-xtra-bein.amagi.tv/playlist.m3u8", "ref": "", "proxy": False},
            {"label": "سيرفر 2 (720p)", "url": "https://bein-esp-xtra.amagi.tv/playlist.m3u8", "ref": "", "proxy": False},
            {"label": "سيرفر 3 (بروكسي)", "url": "https://bein-xtra-bein.amagi.tv/playlist.m3u8", "ref": "", "proxy": True}
        ]
    },
    {
        "id": "bein_xtra2", "bouquet": "bein_fhd",
        "name": "beIN SPORTS XTRA 2 LaLiga/Euro",
        "badge": "1080p FHD", "logo": "🟣",
        "servers": [
            {"label": "سيرفر 1 (1080p)", "url": "https://bein-esp-xtra.amagi.tv/playlist.m3u8", "ref": "", "proxy": False},
            {"label": "سيرفر 2 (720p)", "url": "https://bein-xtra-bein.amagi.tv/playlist.m3u8", "ref": "", "proxy": False}
        ]
    },
    {
        "id": "bein_1", "bouquet": "bein_fhd",
        "name": "beIN SPORTS 1 HD",
        "badge": "Multi-Server", "logo": "🟣",
        "servers": [
            {"label": "سيرفر 1 (FHD)", "url": "https://tvsen6.aynaott.com/beinsports/index.m3u8", "ref": "", "proxy": False},
            {"label": "سيرفر 2 (HD)", "url": "https://ctrl.laotv.la/live/Bsport1/index.m3u8", "ref": "", "proxy": False},
            {"label": "سيرفر 3 (بروكسي)", "url": "http://primetv.cc.cd/beinfhd11/tracks-v1a1/mono.tbin.m3u8", "ref": "", "proxy": True},
            {"label": "سيرفر 4 (XTRA Backup)", "url": "https://bein-xtra-bein.amagi.tv/playlist.m3u8", "ref": "", "proxy": False}
        ]
    },
    {
        "id": "bein_2", "bouquet": "bein_fhd",
        "name": "beIN SPORTS 2 HD",
        "badge": "Multi-Server", "logo": "🟣",
        "servers": [
            {"label": "سيرفر 1 (FHD)", "url": "https://andro.mangeinde4.lat/checklist/androstreamlivebs2.m3u8", "ref": "", "proxy": False},
            {"label": "سيرفر 2 (بروكسي)", "url": "http://primetv.cc.cd/beinfhd22/index.m3u8", "ref": "", "proxy": True},
            {"label": "سيرفر 3 (XTRA Backup)", "url": "https://bein-esp-xtra.amagi.tv/playlist.m3u8", "ref": "", "proxy": False}
        ]
    },
    {
        "id": "bein_3", "bouquet": "bein_fhd",
        "name": "beIN SPORTS 3 HD",
        "badge": "Multi-Server", "logo": "🟣",
        "servers": [
            {"label": "سيرفر 1 (بروكسي)", "url": "http://primetv.cc.cd/beinfhd33/index.m3u8", "ref": "", "proxy": True},
            {"label": "سيرفر 2 (HD)", "url": "https://bein-xtra-bein.amagi.tv/playlist.m3u8", "ref": "", "proxy": False}
        ]
    },
    {
        "id": "bein_max1", "bouquet": "bein_fhd",
        "name": "beIN SPORTS MAX 1 (البطولات القارية)",
        "badge": "EURO / Nations", "logo": "🟣",
        "servers": [
            {"label": "سيرفر 1 (HD)", "url": "https://andro.mangeinde4.lat/checklist/androstreamlivebsm1.m3u8", "ref": "", "proxy": False},
            {"label": "سيرفر 2 (بروكسي)", "url": "http://maxshowplayer.online:2052/live/17810359400475/39215025645488/677040.m3u8", "ref": "", "proxy": True},
            {"label": "سيرفر 3 (FHD)", "url": "https://bein-xtra-bein.amagi.tv/playlist.m3u8", "ref": "", "proxy": False}
        ]
    },
    {
        "id": "bein_low", "bouquet": "bein_low",
        "name": "beIN SPORTS Low-Data (للإنترنت الضعيف)",
        "badge": "240p / 360p", "logo": "🛡️",
        "servers": [
            {"label": "سيرفر توفير البيانات 1", "url": "https://bein-xtra-bein.amagi.tv/playlist.m3u8", "ref": "", "proxy": False, "force_low": True},
            {"label": "سيرفر توفير البيانات 2", "url": "https://bein-esp-xtra.amagi.tv/playlist.m3u8", "ref": "", "proxy": False, "force_low": True}
        ]
    },
    # باقة القنوات الرياضية العربية المفتوحة
    {
        "id": "arryadia", "bouquet": "arab",
        "name": "الرياضية المغربية (Arryadia TNT HD)",
        "badge": "🇲🇦 المغرب", "logo": "🇲🇦",
        "servers": [
            {"label": "سيرفر 1 (SNRT مباشر)", "url": "https://cdn.live.easybroadcast.io/abr_corp/73_arryadia_k2tgcj0/playlist.m3u8", "ref": "https://snrtlive.ma/", "proxy": False},
            {"label": "سيرفر 2 (LiveMedia HD)", "url": "https://stream-lb.livemediama.com/arryadia/hls/master.m3u8", "ref": "", "proxy": False},
            {"label": "سيرفر 3 (بروكسي SD)", "url": "http://149.100.11.252:8000/play/a065/index.m3u8", "ref": "", "proxy": True}
        ]
    },
    {
        "id": "alkass1", "bouquet": "arab",
        "name": "الكأس الرياضية HD (Alkass Sports)",
        "badge": "🇶🇦 قطر", "logo": "🇶🇦",
        "servers": [
            {"label": "سيرفر 1 (Alkass HD)", "url": "https://liveeu-gcp.alkassdigital.net/alkass9-p/main.m3u8", "ref": "https://qmc.qa/", "proxy": True},
            {"label": "سيرفر 2 (Alkass Shoof)", "url": "https://liveakgr.alkassdigital.net/hls/live/2097037/Alkass6Shoof1/master.m3u8", "ref": "", "proxy": False}
        ]
    },
    {
        "id": "adsports1", "bouquet": "arab",
        "name": "أبوظبي الرياضية 1 HD (AD Sports 1)",
        "badge": "🇦🇪 الإمارات", "logo": "🇦🇪",
        "servers": [
            {"label": "سيرفر 1 (مباشر FHD)", "url": "https://admdn1.cdn.mangomolo.com/adsports1/smil:adsports1.stream.smil/playlist.m3u8", "ref": "", "proxy": False},
            {"label": "سيرفر 2 (بروكسي)", "url": "https://admdn1.cdn.mangomolo.com/adsports1/smil:adsports1.stream.smil/playlist.m3u8", "ref": "https://adsports.ae/", "proxy": True}
        ]
    },
    {
        "id": "adsports2", "bouquet": "arab",
        "name": "أبوظبي الرياضية 2 HD (AD Sports 2)",
        "badge": "🇦🇪 الإمارات", "logo": "🇦🇪",
        "servers": [
            {"label": "سيرفر 1 (مباشر FHD)", "url": "https://admdn5.cdn.mangomolo.com/adsports2/smil:adsports2.stream.smil/playlist.m3u8", "ref": "", "proxy": False}
        ]
    },
    {
        "id": "dubaisports1", "bouquet": "arab",
        "name": "دبي الرياضية 1 HD (Dubai Sports 1)",
        "badge": "🇦🇪 الإمارات", "logo": "🇦🇪",
        "servers": [
            {"label": "سيرفر 1 (مباشر FHD)", "url": "https://dmitnthvll.cdn.mangomolo.com/dubaisports/smil:dubaisports.stream.smil/playlist.m3u8", "ref": "", "proxy": False}
        ]
    },
    {
        "id": "sharjah_sp", "bouquet": "arab",
        "name": "الشارقة الرياضية HD (Sharjah Sports)",
        "badge": "🇦🇪 الإمارات", "logo": "🇦🇪",
        "servers": [
            {"label": "سيرفر 1 (مباشر HD)", "url": "https://svs.itworkscdn.net/smc4sportslive/smc4.smil/playlist.m3u8", "ref": "", "proxy": False}
        ]
    },
    {
        "id": "oman_sp", "bouquet": "arab",
        "name": "عمان الرياضية HD (Oman Sport)",
        "badge": "🇴🇲 عمان", "logo": "🇴🇲",
        "servers": [
            {"label": "سيرفر 1 (مباشر HD)", "url": "https://partneta.cdn.mgmlcdn.com/omsport/smil:omsport.stream.smil/playlist.m3u8", "ref": "", "proxy": False}
        ]
    },
    {
        "id": "bahrain_sp", "bouquet": "arab",
        "name": "البحرين الرياضية HD (Bahrain Sport)",
        "badge": "🇧🇭 البحرين", "logo": "🇧🇭",
        "servers": [
            {"label": "سيرفر 1 (مباشر HD)", "url": "https://5c7b683162943.streamlock.net/live/ngrp:bahrainsport1_all/playlist.m3u8", "ref": "", "proxy": False}
        ]
    },
    # باقة القنوات العالمية والأوروبية 24/7
    {
        "id": "fifaplus", "bouquet": "global",
        "name": "FIFA+ Global Football TV",
        "badge": "1080p 24/7", "logo": "🏆",
        "servers": [
            {"label": "سيرفر FIFA الرسمي", "url": "https://a62dad94.wurl.com/master/f36d25e7e52f1ba8d7e56eb859c636563214f541/UmFrdXRlblRWLWV1X0ZJRkFQbHVzRUVuZ2xpc2hITFM/playlist.m3u8", "ref": "", "proxy": False}
        ]
    },
    {
        "id": "rmtv", "bouquet": "global",
        "name": "Real Madrid TV HD (قناة ريال مدريد)",
        "badge": "1080p 24/7", "logo": "🇪🇸",
        "servers": [
            {"label": "سيرفر النادي الرسمي", "url": "https://rmtv.akamaized.net/hls/live/2043153/rmtv-es-web/master.m3u8", "ref": "", "proxy": False}
        ]
    },
    {
        "id": "redbull", "bouquet": "global",
        "name": "Red Bull Sports TV FHD",
        "badge": "1080p 24/7", "logo": "⚽",
        "servers": [
            {"label": "سيرفر Akamai السريع", "url": "https://rbmn-live.akamaized.net/hls/live/590964/BoRB-AT/master.m3u8", "ref": "", "proxy": False}
        ]
    },
    {
        "id": "unite8", "bouquet": "global",
        "name": "Unite8 Sports 1 HD",
        "badge": "1080p 24/7", "logo": "🌍",
        "servers": [
            {"label": "سيرفر مباشر FHD", "url": "https://fta.ektv.in/live/263/master.m3u8", "ref": "", "proxy": False}
        ]
    }
]

MATCH_CACHE = {}

def get_morocco_date_str(offset_days=0):
    """حساب تاريخ اليوم الدقيق بتوقيت المغرب (UTC+1) بصيغة YYYYMMDD"""
    ma_now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1, days=offset_days)
    return ma_now.strftime("%Y%m%d"), ma_now.strftime("%Y-%m-%d")

def format_kickoff_morocco(iso_str):
    """تحويل وقت انطلاق المباراة من UTC إلى توقيت المغرب (GMT+1)"""
    try:
        dt = datetime.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        ma_dt = dt + datetime.timedelta(hours=1)
        return ma_dt.strftime("%H:%M")
    except Exception:
        return ""

def fetch_matches_by_date_and_league(league_code="all", day_offset=0):
    """جلب مباريات اليوم الفعلي (أو أمس/غداً) بدقة تامة شاملة دوري الأمم الأوروبية وكأس أوروبا"""
    date_compact, date_readable = get_morocco_date_str(day_offset)
    cache_key = f"{league_code}_{date_compact}"
    now = time.time()
    if cache_key in MATCH_CACHE and now - MATCH_CACHE[cache_key]["ts"] < 40:
        return MATCH_CACHE[cache_key]["data"], date_readable

    codes = [league_code] if league_code != "all" else [
        "uefa.nations", "uefa.euro", "uefa.euroq", "uefa.champions", "uefa.europa",
        "eng.1", "esp.1", "ita.1", "ger.1", "fra.1",
        "caf.nations", "caf.champions", "caf.confed",
        "fifa.worldq.caf", "fifa.worldq.uefa", "fifa.friendly", "ksa.1", "all"
    ]
    seen_ids = set()
    results = []

    for code in codes:
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={date_compact}"
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                continue
            js = r.json()
            default_lname = (js.get("leagues", [{}])[0].get("name")) or code.upper()
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
                kickoff_ma = format_kickoff_morocco(ev.get("date", ""))

                if state == "in":
                    status_badge = f"🔴 مباشر ({detail})"
                elif state == "post":
                    status_badge = "✅ انتهت"
                else:
                    status_badge = f"🕒 {kickoff_ma} بتوقيت المغرب" if kickoff_ma else f"🕒 {detail}"

                results.append({
                    "id": ev_id,
                    "league": default_lname,
                    "home": home,
                    "away": away,
                    "h_logo": h_logo,
                    "a_logo": a_logo,
                    "score": f"{h_score} - {a_score}" if state != "pre" else (kickoff_ma or "VS"),
                    "status": status_badge,
                    "state": state,
                    "broadcaster": "beIN SPORTS HD / الرياضية"
                })
        except Exception:
            continue

    order_map = {"in": 0, "pre": 1, "post": 2}
    results.sort(key=lambda x: order_map.get(x["state"], 3))
    MATCH_CACHE[cache_key] = {"ts": now, "data": results}
    return results, date_readable

@app.route("/api/matches")
def api_matches():
    league = request.args.get("league", "all")
    day_offset = int(request.args.get("offset", "0"))
    matches, date_str = fetch_matches_by_date_and_league(league, day_offset)
    return jsonify({"date": date_str, "count": len(matches), "matches": matches})

@app.route("/api/channels")
def api_channels():
    return jsonify(YACINE_BOUQUETS)

@app.route("/proxy/stream")
def proxy_stream():
    target_url = request.args.get("url", "")
    custom_ref = request.args.get("ref", "")
    if not target_url:
        return "Missing url", 400
    try:
        target_url = target_url.replace("playlist_dvr.m3u8", "playlist.m3u8")
        ref_to_use = custom_ref if custom_ref else urllib.parse.urljoin(target_url, "/")
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
            "Referer": ref_to_use,
            "Origin": ref_to_use.rstrip("/"),
            "Accept": "*/*",
            "Connection": "keep-alive"
        }
        is_m3u8_hint = target_url.split("?")[0].endswith(".m3u8") or target_url.split("?")[0].endswith(".smil")
        if is_m3u8_hint:
            r = requests.get(target_url, headers=headers, timeout=10, verify=False)
            final_base = r.url.rsplit("/", 1)[0] + "/"
            rewritten = []
            for line in r.text.splitlines():
                s = line.strip()
                if not s:
                    continue
                if s.startswith("#"):
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
                headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "no-store, no-cache, must-revalidate"}
            )
        else:
            req = requests.get(target_url, headers=headers, timeout=12, stream=True, verify=False)
            def generate():
                for chunk in req.iter_content(chunk_size=32768):
                    if chunk:
                        yield chunk
            return Response(
                stream_with_context(generate()),
                status=req.status_code,
                content_type=req.headers.get("Content-Type", "video/MP2T"),
                headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "public, max-age=15"}
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 502

SVG_POSTER = "data:image/svg+xml;utf8," + urllib.parse.quote(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" width="100%" height="100%">'
    '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#13072e"/><stop offset="100%" stop-color="#051329"/></linearGradient></defs>'
    '<rect width="800" height="450" fill="url(#g)"/>'
    '<circle cx="400" cy="200" r="46" fill="#9333ea" fill-opacity="0.25" stroke="#a855f7" stroke-width="3"/>'
    '<polygon points="390,180 390,220 422,200" fill="#c084fc"/>'
    '<text x="400" y="285" font-family="sans-serif" font-size="22" font-weight="bold" fill="#ffffff" text-anchor="middle">PulseGoal Ultra • Yacine &amp; Drama Live Edition</text>'
    '<text x="400" y="315" font-family="sans-serif" font-size="14" fill="#cbd5e1" text-anchor="middle">اختر القناة أو السيرفر لبدء المشاهدة بدون تقطيع</text>'
    '</svg>'
)

HTML_UI = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>PulseGoal Ultra v10 — Yacine & Drama Live Edition</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800;900&display=swap" rel="stylesheet">
<style>
  body { font-family: 'Cairo', sans-serif; background: #070510; color: #f8fafc; padding-bottom: 72px; }
  .yacine-header { background: linear-gradient(135deg, #3b0764 0%, #1e1b4b 50%, #0f172a 100%); }
  .card-glow { background: rgba(17, 24, 39, 0.92); border: 1px solid rgba(168, 85, 247, 0.22); }
  .card-glow:hover { border-color: rgba(168, 85, 247, 0.7); }
</style>
</head>
<body class="max-w-5xl mx-auto">

  <!-- شريط علوي بتصميم Yacine TV & Drama Live -->
  <header class="yacine-header p-3.5 rounded-b-3xl shadow-2xl border-b border-purple-500/30 sticky top-0 z-30">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2.5">
        <div class="w-10 h-10 rounded-2xl bg-gradient-to-tr from-purple-600 to-rose-600 flex items-center justify-center font-black text-lg shadow-lg">PG</div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-sm sm:text-base font-black text-white">PulseGoal <span class="text-amber-400">TV Pro</span></h1>
            <span class="text-[10px] bg-rose-600 text-white px-2 py-0.5 rounded-full font-extrabold">Yacine & Drama Style</span>
          </div>
          <p id="active-ch-title" class="text-[11px] text-purple-200 font-bold">🟣 جاري تشغيل: beIN SPORTS XTRA 1 HD</p>
        </div>
      </div>
      <button onclick="toggleM3uModal()" class="px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-black text-xs shadow-lg">
        ➕ كود FG / M3U
      </button>
    </div>
  </header>

  <main class="p-3 space-y-3.5">

    <!-- مشغل البث المدمج مع شريط السيرفرات المتعددة أسفله مباشرة مثل Yacine TV -->
    <div class="card-glow rounded-2xl overflow-hidden shadow-2xl">
      <div class="relative aspect-video bg-black">
        <video id="v" poster='""" + SVG_POSTER + """' class="w-full h-full object-contain bg-black" controls playsinline autoplay muted></video>
        <button id="unmute-btn" onclick="unmuteVideo()" class="absolute bottom-14 right-3 bg-rose-600 hover:bg-rose-500 text-white px-3.5 py-1.5 rounded-xl text-xs font-black shadow-xl z-20">
          🔊 تفعيل الصوت المباشر
        </button>
      </div>

      <!-- أزرار السيرفرات الخاصة بالقناة النشطة + اختيار الدقة -->
      <div class="p-3 bg-slate-950/90 space-y-2.5 border-t border-slate-800">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <div id="channel-servers-bar" class="flex flex-wrap gap-1.5"></div>
          <div class="flex gap-1">
            <button onclick="setQ(-1)" class="px-2.5 py-1 bg-purple-700 rounded-lg text-[11px] font-bold">ABR تلقائي</button>
            <button onclick="setQ(0)" class="px-2.5 py-1 bg-amber-600 rounded-lg text-[11px] font-bold">240p للنت الضعيف</button>
            <button onclick="openVlc()" class="px-2.5 py-1 bg-emerald-700 rounded-lg text-[11px] font-bold">📲 مشغل خارجي</button>
          </div>
        </div>
      </div>
    </div>

    <!-- نافذة إدخال كود M3U / Xtream على طريقة Drama Live -->
    <div id="m3u-modal" class="hidden card-glow p-3.5 rounded-2xl space-y-2.5 border border-amber-500/50">
      <div class="flex justify-between items-center">
        <h3 class="text-xs font-extrabold text-amber-400">🔑 إضافة سيرفر M3U أو قائمة قنوات خاصة (مثل Drama Live):</h3>
        <button onclick="toggleM3uModal()" class="text-xs text-slate-400">✖ إغلاق</button>
      </div>
      <div class="flex gap-1.5">
        <input id="custom-input" type="text" placeholder="الصق رابط ملف .m3u أو رابط قناة .m3u8 هنا..." class="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white">
        <button onclick="loadCustomInput()" class="px-4 py-1.5 bg-amber-500 text-slate-950 rounded-xl text-xs font-black">تفعيل وحفظ</button>
      </div>
    </div>

    <!-- VIEW 1: باقات القنوات المقسمة على طريقة Yacine TV -->
    <section id="sec-tv" class="space-y-3">
      <!-- شريط الباقات (Bouquets) -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <button onclick="filterBouquet('bein_fhd')" id="bq-bein_fhd" class="p-2.5 rounded-2xl bg-purple-700 text-white font-black text-xs shadow-lg flex items-center justify-center gap-1.5">
          <span>🟣</span><span>beIN SPORTS (FHD/HD)</span>
        </button>
        <button onclick="filterBouquet('bein_low')" id="bq-bein_low" class="p-2.5 rounded-2xl bg-slate-900 border border-slate-800 text-amber-400 font-black text-xs flex items-center justify-center gap-1.5">
          <span>🛡️</span><span>beIN (240p نت ضعيف)</span>
        </button>
        <button onclick="filterBouquet('arab')" id="bq-arab" class="p-2.5 rounded-2xl bg-slate-900 border border-slate-800 text-emerald-400 font-black text-xs flex items-center justify-center gap-1.5">
          <span>🇲🇦🇶🇦</span><span>القنوات العربية المفتوحة</span>
        </button>
        <button onclick="filterBouquet('global')" id="bq-global" class="p-2.5 rounded-2xl bg-slate-900 border border-slate-800 text-sky-400 font-black text-xs flex items-center justify-center gap-1.5">
          <span>🌍</span><span>قنوات عالمية 24/7</span>
        </button>
      </div>

      <input id="ch-search" oninput="renderChannelsGrid()" type="text" placeholder="🔍 ابحث في القنوات (مثال: beIN, الرياضية، الكأس، أبوظبي، ريال مدريد)..." class="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white">

      <!-- شبكة بطاقات القنوات بأسلوب Yacine TV -->
      <div id="channels-grid" class="grid grid-cols-2 sm:grid-cols-3 gap-2.5"></div>
    </section>

    <!-- VIEW 2: مركز مباريات اليوم الحقيقي (Live Match Center) مع دوري الأمم وكأس أوروبا -->
    <section id="sec-matches" class="hidden space-y-3">
      <!-- أزرار التاريخ: أمس / اليوم / غداً -->
      <div class="grid grid-cols-3 gap-2 bg-slate-900 p-1.5 rounded-2xl border border-slate-800">
        <button onclick="changeMatchDay(-1)" id="day-btn--1" class="py-2 rounded-xl text-xs font-extrabold text-slate-300">📅 مباريات أمس</button>
        <button onclick="changeMatchDay(0)" id="day-btn-0" class="py-2 rounded-xl text-xs font-extrabold bg-purple-600 text-white shadow">🔴 مباريات اليوم</button>
        <button onclick="changeMatchDay(1)" id="day-btn-1" class="py-2 rounded-xl text-xs font-extrabold text-slate-300">📅 مباريات الغد</button>
      </div>

      <!-- شريط تصفية البطولات شاملة دوري الأمم وكأس أوروبا -->
      <div class="flex gap-1.5 overflow-x-auto pb-1">
        <button onclick="selectLeague('all')" class="px-3 py-1.5 rounded-xl bg-purple-600 text-white text-[11px] font-bold shrink-0">🔥 كل البطولات</button>
        <button onclick="selectLeague('uefa.nations')" class="px-3 py-1.5 rounded-xl bg-slate-900 border border-purple-500/40 text-purple-300 text-[11px] font-bold shrink-0">🇪🇺 دوري الأمم الأوروبية</button>
        <button onclick="selectLeague('uefa.euro')" class="px-3 py-1.5 rounded-xl bg-slate-900 border border-amber-500/40 text-amber-300 text-[11px] font-bold shrink-0">🏆 كأس أمم أوروبا EURO</button>
        <button onclick="selectLeague('uefa.champions')" class="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 text-[11px] font-bold shrink-0">⚽ أبطال أوروبا</button>
        <button onclick="selectLeague('eng.1')" class="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 text-[11px] font-bold shrink-0">🏴󠁧󠁢󠁥󠁮󠁧󠁿 الإنجليزي</button>
        <button onclick="selectLeague('esp.1')" class="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 text-[11px] font-bold shrink-0">🇪🇸 الإسباني</button>
        <button onclick="selectLeague('caf.nations')" class="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 text-[11px] font-bold shrink-0">🌍 أفريقيا CAF</button>
        <button onclick="selectLeague('ksa.1')" class="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 text-[11px] font-bold shrink-0">🇸🇦 روشن السعودي</button>
      </div>

      <div id="matches-header-info" class="text-xs font-bold text-emerald-400"></div>
      <div id="matches-list-box" class="grid grid-cols-1 md:grid-cols-2 gap-2.5"></div>
    </section>

  </main>

  <!-- شريط تنقل سفلي ثابت على غرار تطبيقات البث العالمية -->
  <nav class="fixed bottom-0 inset-x-0 z-40 bg-slate-950/95 backdrop-blur-md border-t border-slate-800 px-4 py-2">
    <div class="max-w-lg mx-auto grid grid-cols-3 gap-2">
      <button onclick="switchBottomNav('tv')" id="nav-tv" class="flex flex-col items-center py-1 rounded-xl text-purple-400 font-extrabold text-xs">
        <span>📺 الباقات والقنوات</span>
      </button>
      <button onclick="switchBottomNav('matches')" id="nav-matches" class="flex flex-col items-center py-1 rounded-xl text-slate-400 font-bold text-xs">
        <span>⚽ جدول المباريات</span>
      </button>
      <button onclick="filterBouquet('all'); switchBottomNav('tv')" id="nav-all" class="flex flex-col items-center py-1 rounded-xl text-slate-400 font-bold text-xs">
        <span>🌐 كل القنوات</span>
      </button>
    </div>
  </nav>

<script>
const v = document.getElementById('v');
let h = null;
let allChannels = """ + str(YACINE_BOUQUETS).replace("True", "true").replace("False", "false") + """;
let curBouquet = 'bein_fhd';
let curChannel = allChannels[1];
let curSrvIdx = 0;
let curLeague = 'all';
let curDayOffset = 0;
let matchesData = [];

function unmuteVideo() {
  v.muted = false;
  v.play().catch(()=>{});
  document.getElementById('unmute-btn').classList.add('hidden');
}

function toggleM3uModal() {
  document.getElementById('m3u-modal').classList.toggle('hidden');
}

function switchBottomNav(tab) {
  document.getElementById('sec-tv').classList.toggle('hidden', tab !== 'tv');
  document.getElementById('sec-matches').classList.toggle('hidden', tab !== 'matches');
  document.getElementById('nav-tv').className = tab === 'tv' ? 'flex flex-col items-center py-1 rounded-xl text-purple-400 font-extrabold text-xs' : 'flex flex-col items-center py-1 rounded-xl text-slate-400 font-bold text-xs';
  document.getElementById('nav-matches').className = tab === 'matches' ? 'flex flex-col items-center py-1 rounded-xl text-purple-400 font-extrabold text-xs' : 'flex flex-col items-center py-1 rounded-xl text-slate-400 font-bold text-xs';
}

function filterBouquet(bq) {
  curBouquet = bq;
  ['bein_fhd', 'bein_low', 'arab', 'global'].forEach(id => {
    const el = document.getElementById('bq-' + id);
    if (el) {
      el.className = (id === bq)
        ? 'p-2.5 rounded-2xl bg-purple-700 text-white font-black text-xs shadow-lg flex items-center justify-center gap-1.5'
        : 'p-2.5 rounded-2xl bg-slate-900 border border-slate-800 text-slate-300 font-bold text-xs flex items-center justify-center gap-1.5';
    }
  });
  renderChannelsGrid();
}

function renderChannelsGrid() {
  const q = (document.getElementById('ch-search').value || '').toLowerCase();
  window.filteredCh = allChannels.filter(c => (curBouquet === 'all' || c.bouquet === curBouquet) && c.name.toLowerCase().includes(q));
  document.getElementById('channels-grid').innerHTML = window.filteredCh.map((c, i) => `
    <div onclick="pickChannel(${i})" class="cursor-pointer card-glow p-3 rounded-2xl flex flex-col justify-between gap-2 transition hover:scale-[1.01]">
      <div class="flex items-center justify-between">
        <span class="text-xl">${c.logo}</span>
        <span class="text-[10px] bg-purple-500/20 text-purple-300 border border-purple-500/30 px-2 py-0.5 rounded-full font-bold">${c.badge}</span>
      </div>
      <div class="font-extrabold text-xs text-white leading-snug">${c.name}</div>
      <div class="flex items-center justify-between pt-1.5 border-t border-slate-800/80 text-[10px] text-emerald-400 font-bold">
        <span>${c.servers.length} سيرفرات نشطة</span>
        <span>تشغيل ▶</span>
      </div>
    </div>
  `).join('');
}

function pickChannel(idx) {
  const c = window.filteredCh[idx];
  if (!c) return;
  curChannel = c;
  curSrvIdx = 0;
  renderServerButtons();
  playCurrentServer(false);
}

function renderServerButtons() {
  if (!curChannel) return;
  document.getElementById('channel-servers-bar').innerHTML = curChannel.servers.map((s, idx) => `
    <button onclick="selectServer(${idx})" class="px-3 py-1 rounded-xl text-[11px] font-extrabold transition ${idx === curSrvIdx ? 'bg-rose-600 text-white shadow' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}">
      📡 ${s.label}
    </button>
  `).join('');
}

function selectServer(idx) {
  curSrvIdx = idx;
  renderServerButtons();
  playCurrentServer(false);
}

function playCurrentServer(triedProxyFallback) {
  if (!curChannel || !curChannel.servers.length) return;
  const srv = curChannel.servers[curSrvIdx] || curChannel.servers[0];
  document.getElementById('active-ch-title').textContent = `📺 ${curChannel.name} — ${srv.label}`;

  const mustProxy = srv.proxy || srv.url.startsWith('http://') || Boolean(srv.ref) || triedProxyFallback;
  const playUrl = mustProxy
    ? ('/proxy/stream?url=' + encodeURIComponent(srv.url) + '&ref=' + encodeURIComponent(srv.ref || ''))
    : srv.url;

  if (Hls.isSupported()) {
    if (h) h.destroy();
    h = new Hls({
      maxBufferLength: 35,
      maxMaxBufferLength: 60,
      manifestLoadingTimeOut: 9000
    });
    h.loadSource(playUrl);
    h.attachMedia(v);
    h.on(Hls.Events.MANIFEST_PARSED, () => {
      if (srv.force_low) h.currentLevel = 0;
      v.play().catch(()=>{});
    });
    h.on(Hls.Events.ERROR, (ev, data) => {
      if (data.fatal) {
        if (!triedProxyFallback && !mustProxy) {
          playCurrentServer(true);
        } else if (curSrvIdx + 1 < curChannel.servers.length) {
          curSrvIdx++;
          renderServerButtons();
          playCurrentServer(false);
        }
      }
    });
  } else if (v.canPlayType('application/vnd.apple.mpegurl')) {
    v.src = playUrl;
    v.play().catch(()=>{});
  }
}

function setQ(lvl) { if (h) h.currentLevel = lvl; }
function openVlc() {
  if (!curChannel) return;
  const srv = curChannel.servers[curSrvIdx] || curChannel.servers[0];
  window.open(srv.url, '_blank');
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
        if (l.startsWith('#EXTINF:')) name = l.split(',').pop() || 'Custom Channel';
        else if (l.startsWith('http')) {
          allChannels.unshift({
            id: 'cust_' + Math.random(),
            bouquet: 'bein_fhd',
            name: name,
            badge: 'VIP M3U',
            logo: '⭐',
            servers: [{ label: 'سيرفر VIP 1', url: l, ref: '', proxy: l.startsWith('http://') }]
          });
        }
      }
      toggleM3uModal();
      filterBouquet('bein_fhd');
    } catch (e) {}
  } else {
    curChannel = {
      name: 'بث مباشر مخصص',
      servers: [{ label: 'سيرفر مخصص', url: val, ref: '', proxy: val.startsWith('http://') }]
    };
    curSrvIdx = 0;
    renderServerButtons();
    playCurrentServer(false);
    toggleM3uModal();
  }
}

function changeMatchDay(offset) {
  curDayOffset = offset;
  [-1, 0, 1].forEach(d => {
    const b = document.getElementById('day-btn-' + d);
    if (b) {
      b.className = (d === offset)
        ? 'py-2 rounded-xl text-xs font-extrabold bg-purple-600 text-white shadow'
        : 'py-2 rounded-xl text-xs font-extrabold text-slate-300';
    }
  });
  fetchMatches();
}

function selectLeague(code) {
  curLeague = code;
  fetchMatches();
}

async function fetchMatches() {
  document.getElementById('matches-header-info').textContent = '⏳ جاري جلب جدول المباريات الدقيق بتوقيت المغرب...';
  try {
    const res = await fetch(`/api/matches?league=${encodeURIComponent(curLeague)}&offset=${curDayOffset}`);
    const js = await res.json();
    matchesData = js.matches || [];
    document.getElementById('matches-header-info').textContent = `📅 التاريخ: ${js.date} | عدد المباريات: (${js.count}) مباراة`;
    document.getElementById('matches-list-box').innerHTML = matchesData.map(m => `
      <div onclick="switchBottomNav('tv')" class="cursor-pointer card-glow p-3.5 rounded-2xl space-y-2.5">
        <div class="flex items-center justify-between text-[11px]">
          <span class="text-purple-300 font-bold truncate">🏆 ${m.league}</span>
          <span class="${m.state==='in'?'bg-rose-600 text-white':'bg-slate-800 text-amber-300'} px-2.5 py-0.5 rounded-full font-extrabold">${m.status}</span>
        </div>
        <div class="flex items-center justify-between text-xs sm:text-sm font-black text-white py-1">
          <div class="flex items-center gap-2 w-2/5">
            ${m.h_logo ? `<img src="${m.h_logo}" class="w-6 h-6 object-contain">` : '⚽'}
            <span class="truncate">${m.home}</span>
          </div>
          <span class="px-3 py-1 rounded-xl bg-slate-950 border border-purple-500/40 text-amber-400 font-mono text-xs">${m.score}</span>
          <div class="flex items-center justify-end gap-2 w-2/5">
            <span class="truncate text-left">${m.away}</span>
            ${m.a_logo ? `<img src="${m.a_logo}" class="w-6 h-6 object-contain">` : '⚽'}
          </div>
        </div>
        <div class="flex items-center justify-between pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
          <span>📡 القنوات الناقلة: <strong class="text-white">${m.broadcaster}</strong></span>
          <span class="text-emerald-400 font-extrabold">مشاهدة المباراة ▶</span>
        </div>
      </div>
    `).join('');
  } catch (e) {}
}

filterBouquet('bein_fhd');
renderServerButtons();
playCurrentServer(false);
fetchMatches();
</script>
</body></html>"""

@app.route("/")
def index():
    return HTML_UI

@app.route("/health")
def health():
    return jsonify({"status": "online", "edition": "PulseGoal Ultra v10 Yacine & Drama Live Style"}), 200

def build_persistent_reply_kb():
    rk = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    rk.add(
        KeyboardButton("📺 فتح تطبيق البث (Yacine & Drama Style)", web_app=WebAppInfo(url=WEBAPP_URL)),
        KeyboardButton("🔴 مباريات اليوم المباشرة")
    )
    rk.add(
        KeyboardButton("🇪🇺 دوري الأمم الأوروبية وكأس أوروبا"),
        KeyboardButton("🟣 باقات beIN SPORTS (FHD/HD/240p)")
    )
    rk.add(
        KeyboardButton("🇲🇦🇶🇦 القنوات الرياضية العربية"),
        KeyboardButton("🏆 تصفح جميع البطولات")
    )
    return rk

def build_matches_inline_kb(matches, date_str, page=0, per_page=8, league="all", offset=0):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("📺 فتح تطبيق البث (Yacine TV & Drama Live Style)", web_app=WebAppInfo(url=WEBAPP_URL)))

    total = len(matches)
    start = page * per_page
    end = start + per_page
    for m in matches[start:end]:
        txt = f"{m['home']} ({m['score']}) {m['away']} | {m['status']}"
        kb.add(InlineKeyboardButton(txt[:64], web_app=WebAppInfo(url=WEBAPP_URL)))

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"mp_{league}_{offset}_{page-1}"))
    if end < total:
        nav.append(InlineKeyboardButton(f"التالي ({end+1}-{min(end+per_page, total)} من {total}) ➡️", callback_data=f"mp_{league}_{offset}_{page+1}"))
    if nav:
        kb.row(*nav)

    # أزرار تبديل اليوم: أمس / اليوم / غداً مباشرة من تيليغرام
    kb.row(
        InlineKeyboardButton("📅 أمس", callback_data=f"mp_{league}_-1_0"),
        InlineKeyboardButton("🔴 اليوم", callback_data=f"mp_{league}_0_0"),
        InlineKeyboardButton("📅 غداً", callback_data=f"mp_{league}_1_0")
    )
    kb.row(
        InlineKeyboardButton("🇪🇺 دوري الأمم الأوروبية", callback_data="mp_uefa.nations_0_0"),
        InlineKeyboardButton("🏆 كأس أمم أوروبا", callback_data="mp_uefa.euro_0_0")
    )
    kb.row(
        InlineKeyboardButton("🟣 باقات beIN SPORTS", callback_data="menu_bein"),
        InlineKeyboardButton("🏆 كل البطولات", callback_data="menu_leagues")
    )
    return kb

def build_bein_inline_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    for ch in YACINE_BOUQUETS:
        kb.add(InlineKeyboardButton(f"{ch['logo']} {ch['name']}", web_app=WebAppInfo(url=WEBAPP_URL)))
    kb.add(InlineKeyboardButton("🔙 رجوع لجدول مباريات اليوم", callback_data="mp_all_0_0"))
    return kb

def build_leagues_inline_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(*[InlineKeyboardButton(name, callback_data=f"mp_{code}_0_0") for code, name in LEAGUES])
    kb.add(InlineKeyboardButton("🔙 رجوع لمباريات اليوم", callback_data="mp_all_0_0"))
    return kb

if bot:
    @bot.message_handler(commands=["start", "help"])
    def cmd_start(msg):
        bot.send_message(
            msg.chat.id,
            "⚽ <b>مرحباً بك في PulseGoal Ultra v10.0 — إصدار Yacine TV & Drama Live الاحترافي</b>\n\n"
            "🟣 <b>أبرز التحديثات:</b>\n"
            "• تقسيم الباقات بأسلوب <b>Yacine TV</b> (باقة <code>beIN FHD/HD</code>، باقة <code>beIN 240p للنت الضعيف</code>، القنوات العربية، والقنوات العالمية) مع 4 سيرفرات لكل قناة.\n"
            "• دعم كود وقوائم <b>M3U / FG</b> على طريقة <b>Drama Live</b>.\n"
            "• ضبط تاريخ مباريات اليوم بتوقيت المغرب الدقيق مع إضافة <b>دوري الأمم الأوروبية (UEFA Nations League)</b> و <b>كأس أمم أوروبا (UEFA EURO)</b>.",
            reply_markup=build_persistent_reply_kb()
        )
        matches, date_str = fetch_matches_by_date_and_league("all", 0)
        bot.send_message(
            msg.chat.id,
            f"📅 <b>جدول مباريات اليوم ({date_str} بتوقيت المغرب) — الإجمالي ({len(matches)} مباراة):</b>",
            reply_markup=build_matches_inline_kb(matches, date_str, 0, 8, "all", 0)
        )

    @bot.message_handler(func=lambda m: True)
    def handle_text(msg):
        t = (msg.text or "").strip()
        if "دوري الأمم" in t or "أوروبا" in t:
            matches, date_str = fetch_matches_by_date_and_league("uefa.nations", 0)
            if not matches:
                matches, date_str = fetch_matches_by_date_and_league("all", 0)
            bot.send_message(
                msg.chat.id,
                f"🇪🇺 <b>مباريات دوري الأمم الأوروبية وكأس أوروبا ({date_str}):</b>",
                reply_markup=build_matches_inline_kb(matches, date_str, 0, 8, "uefa.nations", 0)
            )
        elif "beIN" in t or "العربية" in t or "القنوات" in t:
            bot.send_message(
                msg.chat.id,
                "🟣 <b>باقات القنوات الرياضية (بتصميم Yacine TV & Drama Live):</b>",
                reply_markup=build_bein_inline_kb()
            )
        elif "البطولات" in t:
            bot.send_message(
                msg.chat.id,
                "🏆 <b>اختر البطولة لعرض جدول مبارياتها الدقيق:</b>",
                reply_markup=build_leagues_inline_kb()
            )
        else:
            matches, date_str = fetch_matches_by_date_and_league("all", 0)
            bot.send_message(
                msg.chat.id,
                f"🔴 <b>مباريات اليوم ({date_str} بتوقيت المغرب) — ({len(matches)} مباراة):</b>",
                reply_markup=build_matches_inline_kb(matches, date_str, 0, 8, "all", 0)
            )

    @bot.callback_query_handler(func=lambda call: True)
    def handle_cb(call):
        d = call.data or ""
        if d.startswith("mp_"):
            parts = d.split("_")
            league = parts[1]
            offset = int(parts[2])
            page = int(parts[3])
            matches, date_str = fetch_matches_by_date_and_league(league, offset)
            bot.answer_callback_query(call.id, f"📅 {date_str} ({len(matches)} مباراة)")
            try:
                bot.edit_message_text(
                    f"📅 <b>جدول المباريات ({date_str} بتوقيت المغرب) — الإجمالي ({len(matches)} مباراة) — صفحة {page+1}:</b>",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=build_matches_inline_kb(matches, date_str, page, 8, league, offset)
                )
            except Exception:
                pass
        elif d == "menu_bein":
            bot.answer_callback_query(call.id)
            bot.edit_message_text("🟣 <b>باقات القنوات الرياضية (Yacine TV & Drama Live Style):</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=build_bein_inline_kb())
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
    app.run(host="0.0.0.0", port=PORT, threaded=True)
