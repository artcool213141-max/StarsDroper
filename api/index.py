import os, requests
from flask import Flask, request, jsonify
from supabase import create_client

app = Flask(__name__)

# Инициализация
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

# 1. Генерация инвойса (Вызывается из JS, возвращает pay_url)
@app.route('/api/create_stars_pay', methods=['POST'])
def create_stars_pay():
    data = request.get_json() or {}
    uid = str(data.get('user_id', '0'))
    amount = int(data.get('amount', 1))
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/createInvoiceLink"
    payload = {
        "title": "Stars Topup",
        "description": f"Пополнение {amount} звезд",
        "payload": f"uid_{uid}",
        "currency": "XTR",
        "prices": [{"label": "Stars", "amount": amount}]
    }
    
    r = requests.post(url, json=payload)
    resp = r.json()
    
    if resp.get('ok'):
        return jsonify({"pay_url": resp['result']}), 200
    return jsonify(resp), 400

# 2. Webhook (Вызывается Telegram-ом при оплате)
@app.route('/api/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    
    # Pre-checkout (Telegram спрашивает: готов ли бот?)
    if 'pre_checkout_query' in update:
        query_id = update['pre_checkout_query']['id']
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery", 
                      json={"pre_checkout_query_id": query_id, "ok": True})
        return "OK", 200

    # Successful Payment (Оплата прошла, пишем в базу)
    if 'message' in update and 'successful_payment' in update['message']:
        payment = update['message']['successful_payment']
        user_id = update['message']['from']['id']
        amount = payment['total_amount']
        charge_id = payment['telegram_payment_charge_id']
        
        if supabase:
            try:
                supabase.table("payments").insert({
                    "user_id": str(user_id),
                    "amount": amount,
                    "charge_id": charge_id,
                    "status": "paid"
                }).execute()
            except Exception as e:
                print(f"DB Error: {e}")
            
        return "OK", 200

    return "OK", 200

@app.route('/api/crypto-webhook', methods=['POST'])
def crypto_webhook(): return "OK", 200

@app.route('/api/stars-webhook', methods=['POST'])
def stars_webhook(): return "OK", 200

if __name__ == '__main__':
    app.run()
