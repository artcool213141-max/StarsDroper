import os, requests
from flask import Flask, request, jsonify
from supabase import create_client

app = Flask(__name__)

# Инициализация
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
CRYPTO_TOKEN = os.environ.get("CRYPTO_PAY_TOKEN")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

# --- STARS PAYMENT ---
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
    print(f"DEBUG ERROR: {resp}") # Смотри это в логах Vercel, если ошибка
    return jsonify(resp), 400

@app.route('/api/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    
    # Обработка ТОЛЬКО successful_payment (для Stars это единственный верный путь)
    if 'message' in update and 'successful_payment' in update['message']:
        payment = update['message']['successful_payment']
        user_id = str(update['message']['from']['id'])
        stars_bought = payment['total_amount']
        
        try:
            # Upsert пользователя
            res = supabase.table("users").select("stars, is_paid_75").eq("user_id", user_id).maybe_single().execute()
            current = res.data if res.data else {"stars": 0, "is_paid_75": False}
            
            update_data = {
                "user_id": user_id,
                "stars": (current.get('stars', 0)) + stars_bought,
                "is_paid_75": current.get('is_paid_75', False) or (stars_bought == 1)
            }
            supabase.table("users").upsert(update_data).execute()
        except Exception as e:
            print(f"DB Error: {e}")
            
    return "OK", 200

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
    return jsonify(resp), 200 if resp.get('ok') else 400

@app.route('/api/crypto-webhook', methods=['POST'])
def crypto_webhook():
    data = request.get_json()
    if data.get('update_type') == 'invoice_paid':
        payload = data.get('payload', {})
        user_id = str(payload.get('payload'))
        amount = float(payload.get('asset_pay_amount') or 0)
        
        # Обновление баланса
        res = supabase.table("users").select("balance").eq("user_id", user_id).execute()
        if res.data:
            new_bal = float(res.data[0].get('balance') or 0) + amount
            supabase.table("users").update({"balance": new_bal}).eq("user_id", user_id).execute()
        else:
            supabase.table("users").insert({"user_id": user_id, "balance": amount}).execute()
            
    return "OK", 200
