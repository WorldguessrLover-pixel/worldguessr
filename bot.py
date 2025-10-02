import time
import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from leaderboard import fetch_leaderboard, extract_players

# Mémoire des derniers elos vus
last_elos = {}

def send_telegram_message(text):
    """Envoie un message sur Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[ERREUR] envoi Telegram : {e}")

def check_and_notify():
    """Vérifie les changements d’elo et envoie les alertes."""
    global last_elos
    data = fetch_leaderboard()
    players = extract_players(data)

    for name, elo in players:
        if elo >= 8000:
            previous_elo = last_elos.get(name)
            if previous_elo is None:
                last_elos[name] = elo
            elif previous_elo != elo:
                last_elos[name] = elo
                if elo >= 10000:
                    message = f"⚠️ Le joueur {name} est à {elo} elos et vient de changer son elo !"
                else:
                    message = f"Le joueur {name} est à {elo} elos et vient de changer son elo !"
                send_telegram_message(message)

if __name__ == "__main__":
    print("🚀 Bot démarré et prêt à surveiller le leaderboard...")
    while True:
        check_and_notify()
        time.sleep(180)  # vérifie toutes les 3 minutes
