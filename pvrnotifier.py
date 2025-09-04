import requests
import time
import sys

# --------- Config ---------
JWT = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIyNzQzMDczMSIsImlhdCI6MTc1Njk2Mjk1MSwiZXhwIjoxNzU5NTU0OTUxfQ.BfeoAwEK1gH2kFdBMBBBRzULR6wK3P8NNxPrVYoFbIE-k8XNL36wpyaaCfVSfX-rU0H6quyct77pP1_9J4cVCwUX7uIXwLUC6PCAqhD3SQVySK-MJZItJT9e2Mnd6SisL2CYbhC7T860EMfBc1VGXg08ModOYShwLFr_M4L8tOJ-SHCu9gag5TfDGRqdTZIyAIpbSuans9DUtXZFW4RG6T8IYhtrV8wRLylmSajeLa6nStGlEs2G0jSVqejAqpU2VkxPKlGX36KIwLFNNGmN0WwD3oc36G0b9yXwJOkoty6lU6Y2smk0Gw9RIYk2mEwjflpduJs98EN_S1f1wtuM8A"
TELEGRAM_BOT_TOKEN = "8022940530:AAF4AmoGS32Nqiyk-XvShe4wfXxQGV6c1eM"
CHAT_IDS = ["720650381", "1345972178"]  # multiple chat IDs

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
