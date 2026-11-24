import os
import threading
import requests
import telebot
from flask import Flask, jsonify
from main import fetch_number_info

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
API_BASE_URL = os.getenv("API_BASE_URL", "").strip().rstrip("/")
PORT = int(os.getenv("PORT", 8080))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = telebot.TeleBot(BOT_TOKEN)
keepalive_app = Flask(__name__)


@keepalive_app.route("/")
def home():
    return jsonify({"status": "ok", "bot": "running"}), 200


@keepalive_app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


DISPLAY_ORDER = [
    ("Number", "Number"),
    ("SIM Card", "SIM"),
    ("Connection", "Connection"),
    ("Mobile State", "State"),
    ("Country", "Country"),
    ("Hometown", "Hometown"),
    ("Reference City", "Reference City"),
    ("Owner Name", "Owner Name"),
    ("Owner Address", "Owner Address"),
    ("Language", "Language"),
    ("Complaints", "Complaints"),
    ("Tracking History", "Tracking History"),
    ("Tracker ID", "Tracker ID"),
    ("Mobile Locations", "Mobile Locations"),
    ("Tower Locations", "Tower Locations"),
]


def get_lookup_data(phone_number: str) -> tuple[dict, int]:
    if API_BASE_URL:
        resp = requests.get(
            f"{API_BASE_URL}/info",
            params={"number": phone_number},
            timeout=15,
        )
        return resp.json(), resp.status_code
    return fetch_number_info(phone_number)


def format_telegram_message(data: dict) -> str:
    lines = ["📱 Number Lookup Result", ""]
    for key, label in DISPLAY_ORDER:
        val = data.get(key)
        if val and val != "N/A":
            lines.append(f"• {label}: {val}")

    if len(lines) == 2:
        return "No useful details found for this number."
    return "\n".join(lines)


@bot.message_handler(commands=["start", "help"])
def handle_start(message):
    bot.reply_to(
        message,
        "Namaste! Kisi bhi phone number ki info ke liye number bhejein ya command use karein:\n"
        "• Direct number: 9087654321\n"
        "• Command: /check 9087654321",
    )


@bot.message_handler(commands=["check", "info"])
def handle_check_command(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(message, "Usage: /check 9087654321")
        return
    process_lookup(message, parts[1].strip())


@bot.message_handler(func=lambda m: bool(m.text and m.text.strip().lstrip("+").isdigit()))
def handle_plain_number(message):
    process_lookup(message, message.text.strip())


def process_lookup(message, phone_number: str):
    status_msg = bot.reply_to(message, "🔍 Fetching details...")
    try:
        payload, status_code = get_lookup_data(phone_number)
        if status_code != 200 or "error" in payload:
            err_msg = payload.get("error", f"Request failed with HTTP {status_code}")
            bot.edit_message_text(
                f"⚠️ {err_msg}",
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
            )
            return

        formatted = format_telegram_message(payload)
        bot.edit_message_text(
            formatted,
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
        )
    except Exception as exc:
        bot.edit_message_text(
            f"❌ Error: {exc}",
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
        )


def run_web_server():
    keepalive_app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)

