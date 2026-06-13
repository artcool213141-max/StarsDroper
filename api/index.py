import os
import requests
import hmac
import hashlib
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client

app = Flask(__name__)
CORS(app)

# 1. Безопасное получение переменных
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
CRYPTO_PAY_TOKEN = os.environ.get("CRYPTO_PAY_TOKEN")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# 2. Инициализация клиента Supabase с проверкой
if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
    print("ВНИМАНИЕ: Supabase не настроен. Проверьте переменные окружения Vercel!")

def get_or_create_user(user_id):
    if not supabase: 
        return {"user_id": int(user_id), "balance": 0.0, "stars": 0}
    
    try:
        # Пробуем найти
        res = supabase.table('users').select("*").eq('user_id', user_id).execute()
        if res.data: 
            return res.data[0]
        
        # Если нет — создаем
        new_user = {"user_id": int(user_id), "balance": 0.0, "stars": 0}
        supabase.table('users').insert(new_user).execute()
        return new_user
    except Exception as e:
        print(f"Ошибка БД: {e}")
        return {"user_id": int(user_id), "balance": 0.0, "stars": 0}

@app.route('/api/create_pay', methods=['POST'])
def create_pay():
    data = request.json
    uid = str(data.get('user_id'))
    amount = str(data.get('amount'))
    
    r = requests.post("https://pay.crypt.bot/api/createInvoice", 
        json={"asset": "TON", "amount": amount, "payload": uid},
        headers={"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}).json()
    
    if r.get('ok'):
        return jsonify({"pay_url": r['result']['bot_invoice_url']})
    return jsonify({"error": "crypto_err"}), 400

@app.route('/api/create_stars_pay', methods=['POST'])
def create_stars_pay():
    data = request.json
    uid = str(data.get('user_id'))
    amount = int(data.get('amount'))
    
    # Запрос к Telegram
    r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/createInvoiceLink", json={
        "title": "Stars", 
        "description": "Пополнение баланса", 
        "payload": uid, 
        "currency": "XTR", 
        "prices": [{"label": "Stars", "amount": amount}]
    })
    
    res_data = r.json()
    
    if res_data.get('ok'):
        # Возвращаем именно строку-ссылку
        return jsonify({"pay_url": res_data['result']})
    else:
        # Логируем ошибку, чтобы понять, почему не работает
        print(f"Telegram API Error: {res_data}")
        return jsonify({"error": "stars_err", "details": res_data}), 400

@app.route('/api/crypto-webhook', methods=['POST'])
def crypto_webhook():
    signature = request.headers.get('crypto-pay-api-signature')
    secret = hashlib.sha256(CRYPTO_PAY_TOKEN.encode()).digest()
    
    if hmac.new(secret, request.data, hashlib.sha256).hexdigest() != signature:
        return "Unauthorized", 401
    
    update = request.json
    if update.get('update_type') == 'invoice_paid':
        p = update['update_object']
        uid, amt = str(p['payload']), float(p['amount'])
        u = get_or_create_user(uid)
        if supabase:
            supabase.table('users').update({"balance": round(float(u.get('balance', 0)) + amt, 2)}).eq('user_id', uid).execute()
    return "OK", 200

@app.route('/api/telegram-webhook', methods=['POST'])
def telegram_webhook():
    update = request.json
    if "pre_checkout_query" in update:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery", 
            json={"pre_checkout_query_id": update["pre_checkout_query"]["id"], "ok": True})
    elif "message" in update and "successful_payment" in update["message"]:
        pay = update["message"]["successful_payment"]
        uid, amt = str(pay['invoice_payload']), int(pay["total_amount"])
        u = get_or_create_user(uid)
        if supabase:
            supabase.table('users').update({"stars": int(u.get('stars', 0)) + amt}).eq('user_id', uid).execute()
    return "OK", 200

# Это критически важно для Vercel
if __name__ == '__main__':
    app.run()
