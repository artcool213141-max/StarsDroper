import os, requests, json
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

def update_db(uid, bal=0, stars=0):
    uid = str(uid)
    try:
        res = supabase.table('users').select("*").eq('user_id', uid).execute()
        if not res.data:
            supabase.table('users').insert({"user_id": uid, "balance": float(bal), "stars": int(stars)}).execute()
        else:
            u = res.data[0]
            new_bal = round(float(u.get('balance', 0)) + float(bal), 2)
            new_stars = int(u.get('stars', 0)) + int(stars)
            supabase.table('users').update({"balance": new_bal, "stars": new_stars}).eq('user_id', uid).execute()
    except Exception as e:
        print(f"DB ERROR: {e}")

@app.route('/api/create_pay', methods=['POST'])
def create_pay():
    data = request.json or {}
    uid, amt = str(data.get('user_id')), f"{float(data.get('amount', 0)):.2f}"
    r = requests.post("https://pay.crypt.bot/api/createInvoice", 
        json={"asset": "TON", "amount": amt, "payload": uid},
        headers={"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN})
    return jsonify(r.json())

@app.route('/api/create_stars_pay', methods=['POST'])
def create_stars_pay():
    data = request.json or {}
    uid, amt = str(data.get('user_id')), int(data.get('amount', 0))
    r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/createInvoiceLink", json={
        "title": "Stars", "payload": uid, "currency": "XTR", "prices": [{"label": "Stars", "amount": amt}]
    })
    return jsonify(r.json())

@app.route('/api/crypto-webhook', methods=['POST'])
def crypto_webhook():
    update = request.json or {}
    if update.get('update_type') == 'invoice_paid':
        p = update.get('update_object', {})
        update_db(p.get('payload'), bal=p.get('amount', 0))
    return "OK", 200

@app.route('/api/stars-webhook', methods=['POST'])
def stars_webhook():
    update = request.json or {}
    if "message" in update and "successful_payment" in update["message"]:
        pay = update["message"]["successful_payment"]
        update_db(pay.get('invoice_payload'), stars=pay.get("total_amount", 0))
    elif "pre_checkout_query" in update:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery", 
            json={"pre_checkout_query_id": update["pre_checkout_query"]["id"], "ok": True})
    return "OK", 200

if __name__ == '__main__': app.run()
