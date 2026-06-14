import os, requests
from flask import Flask, request, jsonify
from supabase import create_client

app = Flask(__name__)

# Инициализация
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
CRYPTO_TOKEN = os.environ.get("CRYPTO_PAY_TOKEN")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

# Создание инвойса CryptoBot
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

# Вебхук CryptoBot
@app.route('/api/crypto-webhook', methods=['POST'])
def crypto_webhook():
    update = request.get_json()
    
    # Проверяем, что это успешная оплата
    if update.get('update_type') == 'invoice_paid':
        payload = update['payload']
        user_id = str(payload['payload']) # ID пользователя
        amount_ton = float(payload['asset_pay_amount'])
        
        # Например, за 1 TON даем 100 баллов баланса
        balance_to_add = int(amount_ton * 100) 
        
        if supabase:
            try:
                # Ищем пользователя
                res = supabase.table("users").select("balance").eq("user_id", user_id).execute()
                
                if res.data:
                    # Если есть - обновляем (текущий + новый)
                    current_balance = res.data[0].get('balance', 0) or 0
                    new_balance = current_balance + balance_to_add
                    supabase.table("users").update({"balance": new_balance}).eq("user_id", user_id).execute()
                    print(f"DEBUG: Баланс {user_id} обновлен до {new_balance}")
                else:
                    # Если нет - создаем запись
                    supabase.table("users").insert({
                        "user_id": user_id, 
                        "balance": balance_to_add
                    }).execute()
                    print(f"DEBUG: Пользователь {user_id} создан, баланс: {balance_to_add}")
                    
            except Exception as e:
                print(f"Crypto DB Error: {e}")
                
    return "OK", 200
