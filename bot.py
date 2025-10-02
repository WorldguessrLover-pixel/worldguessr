#!/usr/bin/env python3
import os
import time
import json
import requests
from datetime import datetime

# ---------- CONFIG ----------
API_URL = os.getenv("API_URL") or "https://www.worldguessr.com/api/leaderboard"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 180))  # secondes (180 = 3 minutes)
ELO_THRESHOLD = int(os.getenv("ELO_THRESHOLD", 8000))
HIGH_ELO_THRESHOLD = int(os.getenv("HIGH_ELO_THRESHOLD", 10000))
STATE_FILE = os.getenv("STATE_FILE", "last_full.json")
SEND_STARTUP_MESSAGE = os.getenv("SEND_STARTUP_MESSAGE", "false").lower() in ("1", "true", "yes")
# ----------------------------

def log(*args, **kwargs):
    print(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] ", *args, **kwargs)

def send_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log("Telegram not configured (missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID).")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        r = requests.post(url, data=payload, timeout=15)
        r.raise_for_status()
        log("Telegram message sent.")
        return True
    except Exception as e:
        log("Error sending Telegram message:", e)
        return False

def fetch_leaderboard():
    """Récupère la liste du leaderboard depuis l'API. Retourne une liste de dicts."""
    r = requests.get(API_URL, timeout=15)
    r.raise_for_status()
    data = r.json()
    # L'API peut renvoyer {"leaderboard": [...] } ou directement une liste
    if isinstance(data, dict) and "leaderboard" in data:
        return data["leaderboard"]
    if isinstance(data, list):
        return data
    # Si structure inattendue, tenter d'extraire tout ce qui ressemble à une liste
    for v in data.values() if isinstance(data, dict) else []:
        if isinstance(v, list):
            return v
    raise ValueError("Unexpected API response format")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log("Error loading state file:", e)
            return {}
    return {}

def save_state(state_dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log("Error saving state file:", e)

def build_username_rating_map(leaderboard):
    """
    Prend une liste d'objets 'player' et retourne un dict {username: rating}
    Assure la présence de valeurs numériques pour rating (0 si absent).
    """
    m = {}
    for p in leaderboard:
        # champs possibles: username, name ; elo or rating
        username = p.get("username") or p.get("name") or p.get("player") or None
        if not username:
            continue
        # try different keys for rating
        rating = None
        for k in ("elo", "rating", "eloToday", "score"):
            if k in p and p[k] is not None:
                try:
                    rating = int(p[k])
                    break
                except Exception:
                    try:
                        rating = int(float(p[k]))
                        break
                    except Exception:
                        rating = None
        if rating is None:
            # fallback 0
            rating = 0
        m[str(username)] = rating
    return m

def check_once():
    try:
        lb = fetch_leaderboard()
    except Exception as e:
        log("Failed to fetch leaderboard:", e)
        return

    current_map = build_username_rating_map(lb)
    last_map = load_state() or {}

    notifications = []

    # Only notify on rating changes for users present in both old and new
    for username, new_rating in current_map.items():
        old_rating = last_map.get(username)
        if old_rating is None:
            # new user: do not notify (not a "change" relative to previous known)
            continue
        if new_rating != old_rating:
            # changed
            if new_rating >= ELO_THRESHOLD:
                if new_rating >= HIGH_ELO_THRESHOLD:
                    prefix = "⚠️ "
                else:
                    prefix = ""
                msg = f"{prefix}Le joueur {username} qui est à {new_rating} elos vient de changer son elo"
                notifications.append(msg)

    # send notifications
    for msg in notifications:
        send_telegram(msg)

    # save current as last
    save_state(current_map)
    log(f"Check done. {len(notifications)} notification(s) sent. Tracked players: {len(current_map)}")

def main_loop():
    log("Bot starting. CHECK_INTERVAL =", CHECK_INTERVAL, "seconds.")
    if SEND_STARTUP_MESSAGE:
        send_telegram("✅ Bot démarré et prêt à surveiller le leaderboard.")
    # On premier démarrage : si pas d'état, on initialise sans envoyer de notif
    if not os.path.exists(STATE_FILE):
        try:
            lb = fetch_leaderboard()
            initial_map = build_username_rating_map(lb)
            save_state(initial_map)
            log("Initial state saved (no notifications on first run). Tracked players:", len(initial_map))
        except Exception as e:
            log("Could not initialize state on first run:", e)

    while True:
        try:
            check_once()
        except Exception as e:
            log("Unhandled error during check:", e)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()
