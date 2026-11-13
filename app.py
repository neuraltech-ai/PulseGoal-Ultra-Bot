from bot_pulsegoal_ultra import app, poll
import threading

# تشغيل بوت تيليغرام في الخلفية تلقائياً عند إقلاع Gunicorn على Render
threading.Thread(target=poll, daemon=True).start()
