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

@app.route('/api/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    
    if 'message' in update and 'successful_payment' in update['message']:
        user_id = str(update['message']['from']['id'])
        payment = update['message']['successful_payment']
        stars_bought = payment['total_amount']
        
        # ЛОГИКА: 1 звезда = верификация
        # Если пришла 1 звезда, ставим true. Если больше - просто добавляем звезды.
        is_verification = (stars_bought == 1)
        
        try:
            # Получаем текущего юзера
            res = supabase.table("users").select("stars, is_paid_75").eq("user_id", user_id).maybe_single().execute()
            
            if res.data:
                # Обновляем старого
                current_paid = res.data.get('is_paid_75')
                # Если была оплата 1 звезды, is_paid_75 становится True и остается True
                new_paid = True if is_verification else (current_paid == True)
                
                supabase.table("users").update({
                    "stars": (res.data.get('stars') or 0) + stars_bought,
                    "is_paid_75": new_paid
                }).eq("user_id", user_id).execute()
            else:
                # Создаем нового
                supabase.table("users").insert({
                    "user_id": user_id,
                    "stars": stars_bought,
                    "is_paid_75": is_verification
                }).execute()
        except Exception as e:
            print(f"WEBHOOK ERROR: {e}")
            
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
