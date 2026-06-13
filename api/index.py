import os, requests, hmac, hashlib
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client

app = Flask(__name__)
CORS(app)

# Конфиг
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
CRYPTO_PAY_TOKEN = os.environ.get("CRYPTO_PAY_TOKEN")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

def get_or_create_user(user_id):
    if not supabase: return {"user_id": int(user_id), "balance": 0.0, "stars": 0}
    try:
        res = supabase.table('users').select("*").eq('user_id', user_id).execute()
        if res.data: return res.data[0]
        new_user = {"user_id": int(user_id), "balance": 0.0, "stars": 0}
        supabase.table('users').insert(new_user).execute()
        return new_user
    except: return {"user_id": int(user_id), "balance": 0.0, "stars": 0}

@app.route('/api/create_pay', methods=['POST'])
def create_pay():
    data = request.json
    uid, amount = str(data.get('user_id')), str(data.get('amount'))
    r = requests.post("https://pay.crypt.bot/api/createInvoice", 
        json={"asset": "TON", "amount": amount, "payload": uid},
        headers={"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}).json()
    if r.get('ok'): return jsonify({"pay_url": r['result']['bot_invoice_url']})
    print(f"CryptoPay Error: {r}") # Лог для Vercel
    return jsonify({"error": "crypto_err", "details": r.get('error')}), 400

@app.route('/api/create_stars_pay', methods=['POST'])
def create_stars_pay():
    data = request.json
    uid, amount = str(data.get('user_id')), int(data.get('amount'))
    r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/createInvoiceLink", json={
        "title": "Stars", "payload": uid, "currency": "XTR", "prices": [{"label": "Stars", "amount": amount}]
    }).json()
    if r.get('ok'): return jsonify({"pay_url": r['result']})
    print(f"Stars Error: {r}") # СМОТРИ ЭТО В ЛОГАХ VERCEL
    return jsonify({"error": "stars_err", "details": r.get('description')}), 400

@app.route('/api/crypto-webhook', methods=['POST'])
def crypto_webhook():
    sig = request.headers.get('crypto-pay-api-signature')
    secret = hashlib.sha256(CRYPTO_PAY_TOKEN.encode()).digest()
    if not sig or hmac.new(secret, request.data, hashlib.sha256).hexdigest() != sig:
        return "Unauthorized", 401
    
    update = request.json or {}
    if update.get('update_type') == 'invoice_paid':
        p = update.get('update_object', {})
        uid, amt = str(p.get('payload')), float(p.get('amount', 0))
        u = get_or_create_user(uid)
        if supabase:
            supabase.table('users').update({"balance": round(float(u.get('balance', 0)) + amt, 2)}).eq('user_id', uid).execute()
    return "OK", 200

@app.route('/api/telegram-webhook', methods=['POST'])
@app.route('/api/stars-webhook', methods=['POST'])
def telegram_webhook():
    update = request.json or {}
    if "pre_checkout_query" in update:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery", 
            json={"pre_checkout_query_id": update["pre_checkout_query"]["id"], "ok": True})
    elif "message" in update and "successful_payment" in update["message"]:
        pay = update["message"]["successful_payment"]
        uid, amt = str(pay.get('invoice_payload')), int(pay.get("total_amount", 0))
        u = get_or_create_user(uid)
        if supabase:
            supabase.table('users').update({"stars": int(u.get('stars', 0)) + amt}).eq('user_id', uid).execute()
    return "OK", 200

if __name__ == '__main__': app.run()
