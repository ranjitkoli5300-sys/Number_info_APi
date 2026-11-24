# Number Info API + Telegram Bot

## Local Setup
```bash
pip install -r requirements.txt
```

### Run Flask API
```bash
python main.py
```
Test endpoint: `http://localhost:5000/info?number=9087654321`

### Run Telegram Bot
Set environment variables:
- `BOT_TOKEN`: Your Telegram bot token from `@BotFather`
- `API_BASE_URL` (optional): Your deployed Flask API URL (e.g. `https://your-api.vercel.app`). If omitted, the bot runs `fetch_number_info` directly.

```bash
python bot.py
```

## Deployment
- **Flask API (`main.py` + `vercel.json`)**: Deploy on Vercel or Render Web Service.
- **Telegram Bot (`bot.py`)**: Deploy as an always-on worker/service on Render, Koyeb, or a VPS so polling stays active.
