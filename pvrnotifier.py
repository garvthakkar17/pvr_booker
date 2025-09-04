import requests
import time
import sys

# --------- Config ---------
JWT = "PASTE_YOUR_NEW_JWT_HERE"
TELEGRAM_BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"
CHAT_IDS = ["YOUR_CHAT_ID_1", "YOUR_CHAT_ID_2"]

# Telegram notifier
def notify_telegram(message):
    for chat_id in CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": chat_id, "text": message}, timeout=5)
        except Exception as e:
            print(f"Error sending Telegram notification to {chat_id}: {e}")

# Polling logic
url = "https://api3.pvrcinemas.com/api/v1/booking/content/msessions"
headers = {
    "Host": "api3.pvrcinemas.com",
    "Authorization": f"Bearer {JWT}",
    "User-Agent": "Mozilla/5.0"
}
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

print("🚀 Starting 24x7 polling for 4DX shows...")

def get_latest_update_id():
    try:
        updates = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates").json().get("result", [])
        return max([u["update_id"] for u in updates], default=0)
    except:
        return 0

last_update_id = get_latest_update_id()

while True:
    try:
        # Check stop command
        updates = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={last_update_id+1}").json().get("result", [])
        for u in updates:
            last_update_id = u["update_id"]
            text = u.get("message", {}).get("text", "").lower()
            chat_id = str(u.get("message", {}).get("chat", {}).get("id"))
            if text.strip() == "stop" and chat_id in CHAT_IDS:
                notify_telegram("🛑 Ticket checker stopped by user.")
                sys.exit(0)

        # Poll API
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if '"format":"4dx"' in resp.text.lower():
            notify_telegram("🎬 4DX tickets available! Book now!")
        else:
            print("No 4DX shows yet.")

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(10)
