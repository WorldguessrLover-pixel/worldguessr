import os

# Récupération des variables d’environnement depuis Render
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
LEADERBOARD_URL = os.getenv(
    "LEADERBOARD_URL",
    "https://api.worldguessr.com/api/leaderboard?username=undefined&pastDay=undefined&mode=elo"
)
