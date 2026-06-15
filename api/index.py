import os, requests
from flask import Flask, request, jsonify
from supabase import create_client

app = Flask(__name__)

# Инициализация
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
CRYPTO_TOKEN = os.environ.get("CRYPTO_PAY_TOKEN") # Добавили токен крипты!
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

# --- 1. STARS PAYMENT ---
@app.route('/api/create_stars_pay', methods=['POST'])
def create_stars_pay():
    data = request.get_json() or {}
    uid = str(data.get('user_id', '0'))
    amount = int(data.get('amount', 25))
    
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

# --- 1. STARS PAYMENT ---
@app.route('/api/create_stars_pay', methods=['POST'])
def create_stars_pay():
    data = request.get_json() or {}
    uid = str(data.get('user_id', '0'))
    amount = int(data.get('amount', 1))
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/createInvoiceLink"
    
    payload = {
        "title": "Stars Topup",
        "description": "Пополнение баланса Stars",
        "payload": f"uid_{uid}",
        "currency": "XTR",
        "prices": [{"label": "Stars", "amount": amount}]
    }
    
    try:
        r = requests.post(url, json=payload)
        resp = r.json()
        
        if not resp.get('ok'):
            print(f"!!! TELEGRAM API ERROR: {resp}")
            return jsonify({"error": "Telegram API error", "details": resp}), 400
            
        return jsonify({"pay_url": resp['result']}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    
    if 'message' in update and 'successful_payment' in update['message']:
        user_id = str(update['message']['from']['id'])
        stars_bought = update['message']['successful_payment']['total_amount']
        
        is_verification = (stars_bought == 1) 
        
        if supabase:
            try:
                res = supabase.table("users").select("stars, is_paid_75").eq("user_id", user_id).maybe_single().execute()
                
                current_stars = res.data.get('stars', 0) if res.data else 0
                is_already_paid = res.data.get('is_paid_75', False) if res.data else False
                
                update_data = {
                    "user_id": user_id,
                    "stars": current_stars + stars_bought,
                    "is_paid_75": is_already_paid or is_verification
                }
                
                supabase.table("users").upsert(update_data).execute()
            except Exception as e:
                print(f"Database error: {e}")
                return "Internal Error", 500
        
        return "OK", 200

    return "OK", 200
# --- TON (CRYPTOBOT) ---
# --- TON (CRYPTOBOT) ---
@app.route('/api/create_crypto_pay', methods=['POST'])
def create_crypto_pay():
    data = request.get_json() or {}
    uid = str(data.get('user_id'))
    amount = float(data.get('amount'))
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    payload = {"asset": "TON", "amount": str(amount), "payload": uid}
    r = requests.post("https://pay.crypt.bot/api/createInvoice", json=payload, headers=headers)
    resp = r.json()
    if resp.get('ok'):
        return jsonify({"pay_url": resp['result']['pay_url']}), 200
    return jsonify(resp), 400

@app.route('/api/crypto-webhook', methods=['POST', 'GET'])
def crypto_webhook():
    if request.method == 'GET':
        return "Webhook is active!", 200

    data = request.get_json()
    
    # Если это не оплата, просто выходим
    if data.get('update_type') != 'invoice_paid':
        return "OK", 200

    try:
        payload = data.get('payload', {})
        user_id = str(payload.get('payload'))
        
        # Бот может присылать разные ключи для суммы. 
        # Проверяем все варианты: asset_pay_amount или просто amount
        amount_ton = float(payload.get('asset_pay_amount') or payload.get('amount') or 0)
        
        # Обновление базы
        res = supabase.table("users").select("balance").eq("user_id", user_id).execute()
        
        if res.data and len(res.data) > 0:
            old_bal = float(res.data[0].get('balance') or 0)
            new_bal = old_bal + amount_ton
            supabase.table("users").update({"balance": new_bal}).eq("user_id", user_id).execute()
        else:
            supabase.table("users").insert({"user_id": user_id, "balance": amount_ton}).execute()
            
        return "OK", 200
    except Exception as e:
        # Теперь код не упадет, если нет logger
        print(f"CRITICAL ERROR: {str(e)}") 
        return "OK", 200 # Возвращаем 200, чтобы бот не спамил ошибками
