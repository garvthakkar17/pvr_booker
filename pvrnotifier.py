import os
import requests
import time
import sys

# --------- Config from Environment Variables ---------
JWT = os.environ.get("JWT")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Multiple chat IDs
CHAT_IDS = [
    os.environ.get("CHAT_ID_1"),
    os.environ.get("CHAT_ID_2"),
    os.environ.get("CHAT_ID_3"),
    # Add more as needed
]
CHAT_IDS = [c for c in CHAT_IDS if c]

if not JWT or not TELEGRAM_BOT_TOKEN or not CHAT_IDS:
    raise ValueError("Please set JWT, TELEGRAM_BOT_TOKEN, and at least one CHAT_ID_X environment variable.")

# Telegram functions
def notify_telegram(message):
    for chat_id in CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {"chat_id": chat_id, "text": message}
            resp = requests.post(url, data=data)
            if resp.status_code != 200:
                print(f"Failed to send to {chat_id}: {resp.text}")
        except Exception as e:
            print(f"Error sending to {chat_id}: {e}")

def check_stop_command(last_update_id):
    """Check Telegram messages from authorized chats for 'stop' command."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        resp = requests.get(url)
        updates = resp.json().get("result", [])
        for update in updates:
            update_id = update["update_id"]
            if update_id <= last_update_id:
                continue
            message = update.get("message", {})
            message_text = message.get("text", "").lower()
            chat_id = str(message.get("chat", {}).get("id"))
            if message_text.strip() == "stop" and chat_id in CHAT_IDS:
                return True, update_id
            last_update_id = update_id
        return False, last_update_id
    except Exception as e:
        print(f"Error checking Telegram stop command: {e}")
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

print("Starting 24x7 polling for 4DX shows...")

last_update_id = 0  # to track Telegram messages

while True:
    try:
        # 1️⃣ Check if stop command was sent
        stop, last_update_id = check_stop_command(last_update_id)
        if stop:
            print("🛑 Stop command received. Exiting script.")
            notify_telegram("🛑 Ticket checker stopped by user.")
            sys.exit(0)

        # 2️⃣ Poll PVR API
        resp = requests.post(url, json=payload, headers=headers)
        raw_text = resp.text.lower()  # lowercase for reliable match

        if '"format":"4dx"' in raw_text:
            print("✅ 4DX detected! Sending Telegram notification...")
            notify_telegram("🎬 4DX tickets available! Book now!")
        else:
            print("No 4DX shows available yet.")

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(10)
