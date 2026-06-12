import os
import requests
import hmac
import hashlib
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client

app = Flask(__name__)
CORS(app)

# Используем сессию для ускорения запросов
session = requests.Session()

# Конфигурация
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
CRYPTO_PAY_TOKEN = os.environ.get("CRYPTO_PAY_TOKEN")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

# --- API: СОЗДАНИЕ ПЛАТЕЖЕЙ ---

@app.route('/api/create_pay', methods=['POST'])
def create_pay():
    data = request.json
    uid = str(data.get('user_id'))
    amount = data.get('amount')
    
    url = "https://pay.crypt.bot/api/createInvoice"
    payload = {"asset": "TON", "amount": str(amount), "payload": uid, "description": "Пополнение баланса TON"}
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
    
    r = session.post(url, json=payload, headers=headers).json()
    if r.get('ok'):
        return jsonify({"pay_url": r['result']['bot_invoice_url']}), 200
    return jsonify({"error": "crypto_bot_err"}), 400

@app.route('/api/create_stars_pay', methods=['POST'])
def create_stars_pay():
    data = request.json
    uid = str(data.get('user_id'))
    amount = int(data.get('amount'))
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/createInvoiceLink"
    payload = {
        "title": "Пополнение звёзд",
        "description": f"Зачисление {amount} XTR",
        "payload": uid,
        "currency": "XTR",
        "prices": [{"label": "Stars", "amount": amount}]
    }
    r = session.post(url, json=payload).json()
    if r.get('ok'):
        return jsonify({"pay_url": r['result']}), 200
    return jsonify({"error": "stars_err"}), 400

# --- API: ВЕБХУКИ ---

@app.route('/api/crypto-webhook', methods=['POST'])
def crypto_webhook():
    # Проверка подписи безопасности
    signature = request.headers.get('crypto-pay-api-signature')
    secret = hashlib.sha256(CRYPTO_PAY_TOKEN.encode()).digest()
    check = hmac.new(secret, request.data, hashlib.sha256).hexdigest()
    
    if signature != check:
        return "Unauthorized", 401

    update = request.json
    if update.get('update_type') == 'invoice_paid':
        p = update.get('payload', {})
        uid = int(p.get('payload'))
        amt = float(p.get('amount'))
        if supabase:
            supabase.rpc('increment_balance', {"uid": uid, "amount_val": amt}).execute()
    return "OK", 200

@app.route('/api/telegram-webhook', methods=['POST'])
def telegram_webhook():
    update = request.json
    if "pre_checkout_query" in update:
        session.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery", 
                      json={"pre_checkout_query_id": update["pre_checkout_query"]["id"], "ok": True})
        return "OK", 200
    
    if "message" in update and "successful_payment" in update["message"]:
        pay = update["message"]["successful_payment"]
        uid = int(pay.get('invoice_payload'))
        amt = int(pay["total_amount"])
        if supabase:
            supabase.rpc('increment_stars', {"uid": uid, "stars_val": amt}).execute()
    return "OK", 200

@app.route('/api/get_balance/<user_id>', methods=['GET'])
def get_balance(user_id):
    if not supabase: return jsonify({"balance": 0, "stars": 0})
    res = supabase.table('users').select("*").eq('user_id', user_id).execute()
    return jsonify(res.data[0] if res.data else {"balance": 0, "stars": 0}), 200

if __name__ == '__main__':
    app.run(debug=True)
