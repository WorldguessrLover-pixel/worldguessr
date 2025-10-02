import os
import time
import threading
import requests
from flask import Flask
from datetime import datetime, timezone

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Ton token Telegram dans Render
CHAT_ID = os.getenv("CHAT_ID")                # ID du chat à notifier
LEADERBOARD_URL = os.getenv("LEADERBOARD_URL")  # URL du leaderboard à surveiller

# --- FLASK APP ---
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot en ligne et surveille le leaderboard."

@app.route("/ping")
def ping():
    return "pong"

# --- BOT FUNCTION ---
def check_leaderboard():
    try:
        resp = requests.get(LEADERBOARD_URL, timeout=10)
        resp.raise_for_status()

        data = resp.json()  # ← adapter selon ton leaderboard
        message = f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}] Leaderboard : {data}"

        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": message}
        )
        print("✅ Message envoyé sur Telegram")

    except Exception as e:
        print(f"⚠️ Erreur lors du check : {e}")

# --- BACKGROUND LOOP ---
def loop_checker():
    while True:
        check_leaderboard()
        time.sleep(180)  # 3 minutes

# --- MAIN ---
if __name__ == "__main__":
    # Thread pour le bot
    t = threading.Thread(target=loop_checker, daemon=True)
    t.start()

    # Flask écoute sur le port fourni par Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
