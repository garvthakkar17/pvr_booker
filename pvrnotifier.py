import os
import requests
import time
import sys
import threading
from flask import Flask

# --------- Config (set these as Render environment variables) ---------
JWT = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIyNzQzMDczMSIsImlhdCI6MTc1Njk2Mjk1MSwiZXhwIjoxNzU5NTU0OTUxfQ.BfeoAwEK1gH2kFdBMBBBRzULR6wK3P8NNxPrVYoFbIE-k8XNL36wpyaaCfVSfX-rU0H6quyct77pP1_9J4cVCwUX7uIXwLUC6PCAqhD3SQVySK-MJZItJT9e2Mnd6SisL2CYbhC7T860EMfBc1VGXg08ModOYShwLFr_M4L8tOJ-SHCu9gag5TfDGRqdTZIyAIpbSuans9DUtXZFW4RG6T8IYhtrV8wRLylmSajeLa6nStGlEs2G0jSVqejAqpU2VkxPKlGX36KIwLFNNGmN0WwD3oc36G0b9yXwJOkoty6lU6Y2smk0Gw9RIYk2mEwjflpduJs98EN_S1f1wtuM8A"
TELEGRAM_BOT_TOKEN = "8022940530:AAF4AmoGS32Nqiyk-XvShe4wfXxQGV6c1eM"

# Individual chat IDs
CHAT_ID_1 = "720650381"
CHAT_ID_2 = "1345972178"

# Collect chat IDs in a list
CHAT_IDS = [cid for cid in [CHAT_ID_1, CHAT_ID_2] if cid]

if not JWT or not TELEGRAM_BOT_TOKEN or not CHAT_IDS:
    raise ValueError("Please set JWT, TELEGRAM_BOT_TOKEN, and at least one CHAT_ID.")

# Telegram functions
def notify_telegram(message):
    for chat_id in CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {"chat_id": chat_id, "text": message}
            resp = requests.post(url, data=data)
            if resp.status_code != 200:
                print(f"⚠️ Telegram notification failed for {chat_id}: {resp.text}")
        except Exception as e:
            print(f"⚠️ Error sending Telegram notification to {chat_id}: {e}")

def check_stop_command(last_update_id):
    """Check Telegram messages for 'stop' command."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        resp = requests.get(url)
        updates = resp.json().get("result", [])
        for update in updates:
            update_id = update["update_id"]
            if update_id <= last_update_id:
                continue
            message_text = update.get("message", {}).get("text", "").lower()
            chat_id = str(update.get("message", {}).get("chat", {}).get("id"))
            if message_text.strip() == "stop" and chat_id in CHAT_IDS:
                return True, update_id
            last_update_id = update_id
        return False, last_update_id
    except Exception as e:
        print(f"⚠️ Error checking Telegram stop command: {e}")
        return False, last_update_id

# API endpoint
url = "https://api3.pvrcinemas.com/api/v1/booking/content/msessions"

# Headers
headers = {
    "Host": "api3.pvrcinemas.com",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Authorization": f"Bearer {JWT}",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Chain": "PVR",
    "Country": "INDIA",
    "Appversion": "1.0",
    "City": "Ahmedabad",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Platform": "WEBSITE",
    "Origin": "https://www.pvrcinemas.com",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Accept-Encoding": "gzip, deflate, br",
    "Priority": "u=1, i"
}

# Payload
payload = {
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
}

# Initialize last_update_id at startup
def get_latest_update_id():
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        resp = requests.get(url)
        updates = resp.json().get("result", [])
        if updates:
            return max(update["update_id"] for update in updates)
        else:
            return 0
    except Exception as e:
        print(f"⚠️ Error fetching latest update_id: {e}")
        return 0

def poll_pvr():
    print("🚀 Starting 24x7 polling for 4DX Conjuring shows...")
    last_update_id = get_latest_update_id()
    print(f"ℹ️ Ignoring old messages. Last update ID: {last_update_id}")

    while True:
        try:
            # 1️⃣ Check for stop command
            stop, last_update_id = check_stop_command(last_update_id)
            if stop:
                print("🛑 Stop command received. Exiting script.")
                notify_telegram("🛑 Ticket checker stopped by user.")
                sys.exit(0)

            # 2️⃣ Poll PVR API
            resp = requests.post(url, json=payload, headers=headers)
            raw_text = resp.text.lower()

            if '"format":"4dx"' in raw_text and "the conjuring" in raw_text:
                print("✅ 4DX Conjuring detected! Sending Telegram notification...")
                notify_telegram("🎬 ALERT: The Conjuring (4DX) tickets available! Book now!")
            else:
                print("❌ No 4DX Conjuring shows available yet.")

        except Exception as e:
            print(f"⚠️ Error: {e}")

        time.sleep(10)

# Flask app for Render logs
app = Flask(__name__)

@app.route("/")
def home():
    return "🎬 PVR Notifier is running. Check Render logs for activity."

# Start background thread
threading.Thread(target=poll_pvr, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
