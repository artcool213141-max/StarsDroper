import os, requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client

app = Flask(__name__)
CORS(app)

# Инициализация
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
CRYPTO_PAY_TOKEN = os.environ.get("CRYPTO_PAY_TOKEN")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

@app.route('/api/create_pay', methods=['POST'])
def create_pay():
    try:
        data = request.get_json()
        print(f"DEBUG: Input data: {data}")
        
        uid = str(data.get('user_id'))
        amt = f"{float(data.get('amount', 0)):.2f}"
        
        r = requests.post("https://pay.crypt.bot/api/createInvoice", 
            json={"asset": "TON", "amount": amt, "payload": uid},
            headers={"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN})
        
        print(f"DEBUG: Crypto response: {r.status_code} - {r.text}")
        return jsonify(r.json()), r.status_code
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/create_stars_pay', methods=['POST'])
def create_stars_pay():
    try:
        data = request.get_json()
        uid = str(data.get('user_id'))
        amt = int(data.get('amount', 0))
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/createInvoiceLink"
        payload = {
            "title": "Stars", 
            "payload": uid, 
            "currency": "XTR", 
            "prices": [{"label": "Stars", "amount": amt}]
        }
        r = requests.post(url, json=payload)
        
        print(f"DEBUG: Stars response: {r.status_code} - {r.text}")
        return jsonify(r.json()), r.status_code
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Webhooks (оставляем без изменений)
@app.route('/api/crypto-webhook', methods=['POST'])
def crypto_webhook():
    return "OK", 200

@app.route('/api/stars-webhook', methods=['POST'])
def stars_webhook():
    return "OK", 200

if __name__ == '__main__': app.run()
