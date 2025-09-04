import requests
import time
import os
import threading
from flask import Flask
from datetime import date # <-- Import date module

# --------- Initialize Flask App ---------
app = Flask(__name__)

# --------- Config (Hardcoded as requested) ---------
JWT = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIyNzQzMDczMSIsImlhdCI6MTc1Njk2Mjk1MSwiZXhwIjoxNzU5NTU0OTUxfQ.BfeoAwEK1gH2kFdBMBBBRzULR6wK3P8NNxPrVYoFbIE-k8XNL36wpyaaCfVSfX-rU0H6quyct77pP1_9J4cVCwUX7uIXwLUC6PCAqhD3SQVySK-MJZItJT9e2Mnd6SisL2CYbhC7T860EMfBc1VGXg08ModOYShwLFr_M4L8tOJ-SHCu9gag5TfDGRqdTZIyAIpbSuans9DUtXZFW4RG6T8IYhtrV8wRLylmSajeLa6nStGlEs2G0jSVqejAqpU2VkxPKlGX36KIwLFNNGmN0WwD3oc36G0b9yXwJOkoty6lU6Y2smk0Gw9RIYk2mEwjflpduJs98EN_S1f1wtuM8A"
TELEGRAM_BOT_TOKEN = "8022940530:AAF4AmoGS32Nqiyk-XvShe4wfXxQGV6c1eM"
CHAT_IDS = ["720650381", "1345972178"]

# --------- Core Logic ---------

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
    print("Starting 24x7 polling for 4DX shows...")
    
    url = "https://api3.pvrcinemas.com/api/v1/booking/content/msessions"
    
    # ================== UPDATED SECTION START ==================

    # Full headers to mimic a real browser request
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
        "Priority": "u=1, i"
    }
    
    # ================== UPDATED SECTION END ==================
    
    last_update_id = 0
    try:
        updates = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates").json().get("result", [])
        if updates:
            last_update_id = max(u["update_id"] for u in updates)
    except Exception as e:
        print(f"Could not fetch initial update ID: {e}")
    print(f"Starting polling... Last update ID set to: {last_update_id}")

    while True:
        try:
            stop, last_update_id = check_stop_command(last_update_id)
            if stop:
                print("🛑 Stop command received. Exiting script.")
                notify_telegram("🛑 Ticket checker has been stopped by user command.")
                os._exit(0)

            # ================== UPDATED SECTION START ==================
            
            # Get today's date automatically in YYYY-MM-DD format
            
            # Full payload to match your provided request
            payload = {
                "city": "Ahmedabad",
                "mid": "31738",
                "experience": "ALL",
                "specialTag": "ALL",
                "lat": "22.83694592",
                "lng": "72.59033180",
                "lang": "ALL",
                "format": "4DX",
                "dated": "2025-09-04", # Using the dynamic date
                "time": "08:00-24:00",
                "cinetype": "ALL",
                "hc": "ALL",
                "adFree": False
            }
            
            # ================== UPDATED SECTION END ==================
            
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            
            # This check is still useful to confirm the result
            if resp.status_code == 200 and '"format":"4dx"' in resp.text.lower():
                print(f"✅ 4DX detected ! Sending Telegram notification...")
                notify_telegram(f"🎬 4DX tickets are be available! Check PVR now!")
            else:
                print(f"No 4DX shows found Status: {resp.status_code}")

        except Exception as e:
            print(f"An unexpected error occurred in the polling loop: {e}")

        time.sleep(10)

# --------- Flask Web Routes ---------

@app.route('/')
def health_check():
    return "PVR 4DX Checker is running.", 200

# --------- Main Execution ---------

polling_thread = threading.Thread(target=poll_pvr_api, daemon=True)
polling_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)