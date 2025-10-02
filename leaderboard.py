import requests
from config import LEADERBOARD_URL

def fetch_leaderboard():
    """Récupère les données du leaderboard depuis l’API."""
    try:
        response = requests.get(LEADERBOARD_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERREUR] Impossible de récupérer le leaderboard : {e}")
        return []

def extract_players(data):
    """Extrait les joueurs et leur elo depuis l’API."""
    players = []
    try:
        for entry in data.get("leaderboard", []):
            name = entry.get("username")
            elo = entry.get("elo")
            if name and elo:
                players.append((name, elo))
    except Exception as e:
        print(f"[ERREUR] Parsing leaderboard : {e}")
    return players
