import requests
import time
import sys
import json

# --------- Config ---------
# --------- Config ---------
JWT = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIyNzQzMDczMSIsImlhdCI6MTc1Njk5MDI4MywiZXhwIjoxNzU5NTgyMjgzfQ.SAqCdNyZH6XgIrFsS7xjXyLu0kvmhT6hMPb8vd7YMuirXVtniwfpURX7aloNWSWE4z9hd0YysGsgrR-04t1AcFhTD0G4IVALpGIIv1_Adx6NHrWfK8KZ-tHCgU9Q2plp5mwHXnpiylQe2B2S2Byn5qxJ8NueuExAjPoaOTIKP-nI3BJw6wmmZSvTTU7iX30mxXPBd7nXoRc1C_FcdRL2xjgeYXu6U7OQWUHi43QzWh1MyFEf-iucIowrHRlqKxttTD5U0pb80v3_hVzY1CMCKtb8dc5-s5QZxPBCVW8aw849DQnk5Tdpeu02LVrwo_qUQFF8ogmEJai0Vhmcxe5HuQ"
TELEGRAM_BOT_TOKEN = "8022940530:AAF4AmoGS32Nqiyk-XvShe4wfXxQGV6c1eM"

# Individual chat IDs
CHAT_ID_1 = "720650381"
CHAT_ID_2 = "1345972178"
# Add more if needed
CHAT_IDS = [CHAT_ID_1, CHAT_ID_2]


# --- Target Cinema ---
TARGET_CINEMA_NAME = "PVR Acropolis Ahemdabad"


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
                print(f"Telegram notification failed for {chat_id}: {resp.text}")
        except Exception as e:
            print(f"Error sending Telegram notification to {chat_id}: {e}")

def check_stop_command(last_update_id):
    """Check Telegram messages for 'stop' command."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        params = {'offset': last_update_id + 1, 'timeout': 5}
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        updates = resp.json().get("result", [])
        
        new_last_id = last_update_id
        for update in updates:
            update_id = update["update_id"]
            new_last_id = max(new_last_id, update_id)
            
            message = update.get("message", {})
            message_text = message.get("text", "").lower().strip()
            chat_id = str(message.get("chat", {}).get("id"))
            
            if message_text == "stop" and chat_id in CHAT_IDS:
                return True, new_last_id
        return False, new_last_id
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
    "dated": "2025-09-09",
    "time": "08:00-24:00",
    "cinetype": "ALL",
    "hc": "ALL",
    "adFree": False
}

print(f"Starting 24x7 polling for 4DX shows at {TARGET_CINEMA_NAME}...")

def get_latest_update_id():
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        resp = requests.get(url)
        resp.raise_for_status()
        updates = resp.json().get("result", [])
        if updates:
            return max(update["update_id"] for update in updates)
        return 0
    except Exception as e:
        print(f"Error fetching latest update_id: {e}")
        return 0

last_update_id = get_latest_update_id()
print(f"Starting polling... Ignoring old messages. Last update ID: {last_update_id}")

while True:
    try:
        # 1️⃣ Check if stop command was sent
        stop, new_update_id = check_stop_command(last_update_id)
        last_update_id = new_update_id
        if stop:
            print("🛑 Stop command received. Exiting script.")
            notify_telegram("🛑 Ticket checker stopped by user.")
            sys.exit(0)

        # 2️⃣ Poll PVR API
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()

        data = resp.json()
        
        # Safely extract the list of cinema sessions
        movie_sessions = data.get("output", {}).get("movieCinemaSessions", [])
        
        shows_found = False
        if not movie_sessions:
            print("No 'movieCinemaSessions' data found in the response.")
        else:
            # Iterate through all returned cinemas
            for cinema_session in movie_sessions:
                cinema_details = cinema_session.get("cinema", {})
                cinema_name = cinema_details.get("name")

                # Check if this is the target cinema
                if cinema_name == TARGET_CINEMA_NAME:
                    print(f"Found cinema: {cinema_name}. Checking for 4DX shows...")
                    
                    # Now check its experience sessions
                    experience_sessions = cinema_session.get("experienceSessions", [])
                    for exp in experience_sessions:
                        if exp.get("experienceKey") == "4dx" and exp.get("showCount", 0) > 0:
                            show_count = exp.get("showCount")
                            message = f"🎬 4DX tickets available at {TARGET_CINEMA_NAME}! Show count: {show_count}. Book now!"
                            print(f"✅ {message}")
                            notify_telegram(message)
                            shows_found = True
                            break # Exit inner loop
                    
                    if not experience_sessions:
                         print(f"No 'experienceSessions' found for {cinema_name}.")
                
                if shows_found:
                    break # Exit outer loop
        
        if not shows_found:
            print("No 4DX shows available yet.")

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON response: {resp.text}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    # Wait for 10 seconds before the next check
    time.sleep(10)