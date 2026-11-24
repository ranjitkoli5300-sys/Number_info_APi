import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request

app = Flask(__name__)

FIELDS = [
    ("Complaints", "Complaints"),
    ("Owner Name", "Owner Name"),
    ("SIM Card", "SIM card"),
    ("Mobile State", "Mobile State"),
    ("IMEI Number", "IMEI number"),
    ("MAC Address", "MAC address"),
    ("Connection", "Connection"),
    ("IP Address", "IP address"),
    ("Owner Address", "Owner Address"),
    ("Hometown", "Hometown"),
    ("Reference City", "Refrence City"),
    ("Owner Personality", "Owner Personality"),
    ("Language", "Language"),
    ("Mobile Locations", "Mobile Locations"),
    ("Country", "Country"),
    ("Tracking History", "Tracking History"),
    ("Tracker ID", "Tracker Id"),
    ("Tower Locations", "Tower Locations"),
]


def fetch_number_info(phone_number: str) -> tuple[dict, int]:
    cleaned = phone_number.strip()
    if not cleaned:
        return {"error": "Please provide a phone number"}, 400

    if not cleaned.isdigit() and not (cleaned.startswith("+") and cleaned[1:].isdigit()):
        return {"error": "Invalid phone number format"}, 400

    try:
        url = "https://calltracer.in"
        headers = {
            "Host": "calltracer.in",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {
            "country": "IN",
            "q": cleaned,
        }

        response = requests.post(url, headers=headers, data=payload, timeout=10)
        if response.status_code != 200:
            return {"error": f"Failed to fetch data. HTTP {response.status_code}"}, 500

        soup = BeautifulSoup(response.text, "html.parser")

        def get_value(label: str) -> str:
            cell = soup.find(string=lambda t: t and label in t)
            if cell:
                tr = cell.find_parent("tr")
                if tr:
                    tds = tr.find_all("td")
                    if len(tds) > 1:
                        val = tds[1].get_text(" ", strip=True)
                        return val if val else "N/A"
            return "N/A"

        data = {"Number": cleaned}
        for output_key, label_text in FIELDS:
            data[output_key] = get_value(label_text)

        # Check all fields except "Number"
        lookup_values = [v for k, v in data.items() if k != "Number"]
        if all(v == "N/A" for v in lookup_values):
            return {"error": "No data found for this number."}, 404

        return data, 200

    except requests.Timeout:
        return {"error": "Request timed out while fetching number info."}, 504
    except Exception as exc:
        return {"error": str(exc)}, 500


@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "message": "Number Info API is running",
        "usage": "/info?number=PHONE_NUMBER",
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/info", methods=["GET"])
def number_info():
    phone_number = request.args.get("number", "")
    result, status_code = fetch_number_info(phone_number)
    return jsonify(result), status_code


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
