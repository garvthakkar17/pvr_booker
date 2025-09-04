import requests
import time
import os
import threading
from flask import Flask
from datetime import date

app = Flask(__name__)

# --------- Config (Hardcoded) ---------
JWT = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIyNzQzMDczMSIsImlhdCI6MTc1Njk4NTg1NCwiZXhwIjoxNzU5NTc3ODU0fQ.TOxysPewT3bJgOQSWUGcMqERUF7wCPbQ4xFRQjZ9zT7td_psbCHE5oDs2NyWCYOZbmQ5i_A7Cf_TfAP9cQoJMpuNYobn1RRtZDRIC03Lnu0jq4brkbWkZzwN9wMSWOYZwW-RMQ0gPyM8nZuRCmGmdM9_YhOxLxEob_iMLD7I_wL5XhVqr-mL4VtqR80LbUNi5OjXWv2GMSi9quxaipqX_6BgkLs9R4hsUthXgcJBwYhViG__wD_vZ0ooPV5EBQz64s6Qs52TiOJ6flrAaJlq2LvQNnv3aMGT2-uGiXAiEIuPzugr6S03aNH3Ko_ZDaqahA7mDKQPbZKS3aFy4zjXIA"
TELEGRAM_BOT_TOKEN = "8022940530:AAF4AmoGS32Nqiyk-XvShe4wfXxQGV6c1eM"
CHAT_IDS = ["720650381", "1345972178"]

def notify_telegram(message):
    for chat_id in CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {"chat_id": chat_id, "text": message}
            requests.post(url, data=data, timeout=5)
        except Exception as e:
            print(f"Error sending Telegram notification to {chat_id}: {e}")

def check_stop_command(last_update_id):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={last_update_id + 1}"
        resp = requests.get(url, timeout=5)
        updates = resp.json().get("result", [])
        
        new_last_id = last_update_id
        for update in updates:
            new_last_id = update["update_id"]
            message = update.get("message", {})
            message_text = message.get("text", "").lower().strip()
            chat_id = str(message.get("chat", {}).get("id"))
            
            if message_text == "stop" and chat_id in CHAT_IDS:
                return True, new_last_id
                
        return False, new_last_id
    except Exception as e:
        print(f"Error checking Telegram stop command: {e}")
        return False, last_update_id

def poll_pvr_api():
    print("🚀 Starting 24x7 polling for 4DX shows...")
    
    url = "https://api3.pvrcinemas.com/api/v1/booking/content/msessions"
    
    headers = {
        "Host": "api3.pvrcinemas.com",
        "Authorization": f"Bearer {JWT}",
        "Chain": "PVR",
        "City": "Ahmedabad",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/plain, */*",
        "Appversion": "1.0",
        "Platform": "WEBSITE",
        "Origin": "https://www.pvrcinemas.com"
    }
    
    last_update_id = 0
    try:
        updates = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates").json().get("result", [])
        if updates:
            last_update_id = max(u["update_id"] for u in updates)
    except Exception as e:
        print(f"Could not fetch initial update ID: {e}")
    print(f"Starting polling... Last update ID: {last_update_id}")

    while True:
        try:
            stop, last_update_id = check_stop_command(last_update_id)
            if stop:
                print("🛑 Stop command received. Exiting script.")
                notify_telegram("🛑 Ticket checker stopped by user command.")
                os._exit(0)

            today_str = date.today().strftime("%Y-%m-%d")
            payload = {
                "city": "Ahmedabad",
                "mid": "31738",
                "experience": "4DX",   # Set experience to 4DX explicitly
                "specialTag": "ALL",
                "lat": "22.83694592",
                "lng": "72.59033180",
                "lang": "ALL",
                "format": "ALL",
                "dated": today_str,
                "time": "08:00-24:00",
                "cinetype": "ALL",
                "hc": "ALL",
                "adFree": False
            }

            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            
            # Check for 4DX shows
            if resp.status_code == 200 and '"format":"4dx"' in resp.text.lower():
                print(f"✅ 4DX detected! Sending Telegram notification...")
                notify_telegram("🎬 4DX tickets available! Book now!")
            else:
                print(f"No 4DX shows found. Status code: {resp.status_code}")

        except Exception as e:
            print(f"Polling error: {e}")

        time.sleep(10)

@app.route('/')
def health_check():
    return "PVR 4DX Checker running.", 200

# --------- Main ---------
polling_thread = threading.Thread(target=poll_pvr_api, daemon=True)
polling_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
