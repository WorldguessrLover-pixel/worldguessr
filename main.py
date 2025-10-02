import os
import json
import csv
import re
from io import StringIO
from datetime import datetime
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# ---------- CONFIG ----------
CSV_URL = "https://www.worldguessr.com/api/leaderboard"  # API WorldGuessr
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SECRET_KEY = os.getenv("SECRET_KEY") or "changeme"

CHECK_INTERVAL = 180   # toutes les 3 minutes
ELO_THRESHOLD = 8000   # minimum elo pour notifier
HIGH_ELO_THRESHOLD = 10000  # seuil élite (message spécial)
STATE_FILE = "last_full.json"
# ----------------------------

app = Flask(__name__)

# ----------------- Helpers -----------------
def fetch_csv(url):
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.text

def send_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram non configuré.")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        r = requests.post(url, data=payload, timeout=15)
        r.raise_for_status()
        return True
    except Exception as e:
        print("Erreur Telegram:", e)
        return False

def parse_top_n(csv_text, n=1000):
    """Parse le leaderboard (JSON ou CSV)"""
    # Si JSON
    try:
        data = json.loads(csv_text)
        if isinstance(data, list):
            results = []
            for i, player in enumerate(data[:n]):
                results.append({
                    "username": player.get("username") or player.get("name") or f"player{i+1}",
                    "rating": int(player.get("elo") or player.get("rating") or 0),
                    "rank": int(player.get("rank") or i+1)
                })
            return results
    except Exception:
        pass

    # Sinon CSV
    f = StringIO(csv_text)
    reader = csv.DictReader(f)
    results = []
    for i, row in enumerate(reader):
        if i >= n:
            break
        uname = row.get("username") or row.get("user") or row.get("name") or f"player{i+1}"
        rating_raw = row.get("elo") or row.get("rating") or row.get("score") or ""
        try:
            rating = int(re.search(r"-?\d+", rating_raw.replace(",", "")).group()) if rating_raw else None
        except:
            rating = None
        results.append({
            "username": uname.strip(),
            "rating": rating,
            "rank": i + 1
        })
    return results

def load_last_state(state_file):
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_state(state, state_file):
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def compare_states(old, new):
    map_old = {u["username"]: u for u in old} if old else {}
    map_new = {u["username"]: u for u in new} if new else {}

    rating_changes = []
    for username in set(map_old.keys()).intersection(map_new.keys()):
        o = map_old[username]
        n = map_new[username]
        if o.get("rating") is not None and n.get("rating") is not None and o["rating"] != n["rating"]:
            rating_changes.append({
                "username": username,
                "old_rating": o["rating"],
                "new_rating": n["rating"],
                "delta": n["rating"] - o["rating"]
            })
    return rating_changes

# ----------------- Job principal -----------------
def scheduled_check():
    print(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] Running full leaderboard check...")

    try:
        csv_text = fetch_csv(CSV_URL)
    except Exception as e:
        print("Erreur fetch_csv:", e)
        return

    players = parse_top_n(csv_text, n=1000)
    last_state = load_last_state(STATE_FILE) or []

    changes = compare_states(last_state, players)

    for c in changes:
        if c["new_rating"] and c["new_rating"] >= ELO_THRESHOLD:
            if c["new_rating"] >= HIGH_ELO_THRESHOLD:
                msg = f"⚠️ Le joueur {c['username']} qui est à {c['new_rating']} elos vient de changer son elo"
            else:
                msg = f"Le joueur {c['username']} qui est à {c['new_rating']} elos vient de changer son elo"
            send_telegram(msg)

    save_state(players, STATE_FILE)

# ----------------- Scheduler -----------------
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=scheduled_check,
    trigger="interval",
    seconds=CHECK_INTERVAL,
    id="leaderboard_monitor"
)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# ----------------- Flask route -----------------
@app.route("/")
def index():
    return "Bot leaderboard WorldGuessr actif et vérifie toutes les 3 minutes."

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
