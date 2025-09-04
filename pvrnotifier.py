# ===== PATCH FOR PYTHON 3.13 =====
import sys

# Python 3.13 removed 'imghdr', create a dummy module
if "imghdr" not in sys.modules:
    import types
    sys.modules["imghdr"] = types.SimpleNamespace(
        what=lambda *args, **kwargs: None  # dummy function
    )

# ===== IMPORTS =====
import requests
import time
import threading
from flask import Flask
from telegram import Bot
from telegram.ext import Updater, CommandHandler

# ===== CONFIG =====
JWT = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIyNzQzMDczMSIsImlhdCI6MTc1Njk2Mjk1MSwiZXhwIjoxNzU5NTU0OTUxfQ.BfeoAwEK1gH2kFdBMBBBRzULR6wK3P8NNxPrVYoFbIE-k8XNL36wpyaaCfVSfX-rU0H6quyct77pP1_9J4cVCwUX7uIXwLUC6PCAqhD3SQVySK-MJZItJT9e2Mnd6SisL2CYbhC7T860EMfBc1VGXg08ModOYShwLFr_M4L8tOJ-SHCu9gag5TfDGRqdTZIyAIpbSuans9DUtXZFW4RG6T8IYhtrV8wRLylmSajeLa6nStGlEs2G0jSVqejAqpU2VkxPKlGX36KIwLFNNGmN0WwD3oc36G0b9yXwJOkoty6lU6Y2smk0Gw9RIYk2mEwjflpduJs98EN_S1f1wtuM8A"
TELEGRAM_BOT_TOKEN = "8022940530:AAF4AmoGS32Nqiyk-XvShe4wfXxQGV6c1eM"

# Individual chat IDs
CHAT_ID_1 = "720650381"
CHAT_ID_2 = "1345972178"
CHAT_IDS = [cid for cid in [CHAT_ID_1, CHAT_ID_2] if cid]

POLL_INTERVAL = 10  # seconds
stop_flag = False
bot = Bot(TELEGRAM_BOT_TOKEN)

# ===== POLLING THREAD =====
def poll_pvr():
    global stop_flag
    print("🚀 Polling thread started for 4DX Conjuring shows...")
    while True:
        if stop_flag:
            print("⏹️ Polling stopped.")
            break
        try:
            resp = requests.post(
                "https://api3.pvrcinemas.com/api/v1/booking/content/msessions",
                json={
                    "city": "Ahmedabad",
                    "mid": "31738",
                    "experience": "4DX",
                    "specialTag": "ALL",
                    "lat": "22.83694592",
                    "lng": "72.59033180",
                    "lang": "ALL",
                    "format": "ALL",
                    "dated": "2025-09-07",
                    "time": "08:00-24:00",
                    "cinetype": "ALL",
                    "hc": "ALL",
                    "adFree": False
                },
                headers={
                    "Authorization": f"Bearer {JWT}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            text = resp.text.lower()
            if '"format":"4dx"' in text and "the conjuring" in text:
                msg = "🎬 ALERT: The Conjuring (4DX) tickets available! Book now!"
                print(msg)
                for chat_id in CHAT_IDS:
                    try:
                        bot.send_message(chat_id=chat_id, text=msg)
                    except Exception as e:
                        print(f"⚠️ Telegram send failed for {chat_id}: {e}")
            else:
                print("❌ No 4DX Conjuring shows yet.")
        except Exception as e:
            print(f"⚠️ PVR polling error: {e}")
        time.sleep(POLL_INTERVAL)

# ===== TELEGRAM COMMAND =====
def stop(update, context):
    global stop_flag
    stop_flag = True
    update.message.reply_text("⏹️ Polling stopped by user.")

# ===== FLASK APP =====
app = Flask(__name__)
@app.route("/")
def index():
    return "✅ PVR Notifier running. Check logs for activity."

# ===== MAIN =====
if __name__ == "__main__":
    # Start polling in background thread
    threading.Thread(target=poll_pvr, daemon=True).start()
    
    # Start Flask in a separate thread
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()
    
    # Telegram Updater runs in main thread
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("stop", stop))
    updater.start_polling()
    updater.idle()
