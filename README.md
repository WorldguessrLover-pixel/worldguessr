# Bot Telegram WorldGuessr Leaderboard

Ce bot surveille le leaderboard de WorldGuessr toutes les 3 minutes.  

## Fonctionnalités
- Si un joueur change son Elo **au-dessus de 8000** → notification Telegram
- Si un joueur change son Elo **au-dessus de 10000** → notification Telegram avec ⚠️

## Variables d'environnement à définir sur Render
- `TELEGRAM_BOT_TOKEN` : token de ton bot Telegram
- `TELEGRAM_CHAT_ID` : ID du chat ou groupe
- `SECRET_KEY` : clé secrète (au choix)
