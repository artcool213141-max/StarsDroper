import os, requests
from flask import Flask, request, jsonify
from supabase import create_client

app = Flask(__name__)

# Инициализация
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

# 1. Генерация инвойса
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

# 2. Webhook (обновляет баланс в таблице 'users')
@app.route('/api/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    
    # Pre-checkout
    if 'pre_checkout_query' in update:
        query_id = update['pre_checkout_query']['id']
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery", 
                      json={"pre_checkout_query_id": query_id, "ok": True})
        return "OK", 200

    # Successful Payment
    if 'message' in update and 'successful_payment' in update['message']:
        payment = update['message']['successful_payment']
        user_id = str(update['message']['from']['id'])
        stars_bought = payment['total_amount']
        
        if supabase:
            try:
                # 1. Получаем текущее значение
                response = supabase.table("users").select("stars").eq("user_id", user_id).execute()
                
                if response.data:
                    # Если пользователь есть - прибавляем
                    current_stars = response.data[0].get('stars', 0)
                    new_balance = current_stars + stars_bought
                    supabase.table("users").update({"stars": new_balance}).eq("user_id", user_id).execute()
                else:
                    # Если нет - создаем
                    supabase.table("users").insert({"user_id": user_id, "stars": stars_bought}).execute()
                
                print(f"DEBUG: Баланс пользователя {user_id} обновлен на +{stars_bought}")
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


# --- ЭТО ДОБАВИТЬ В КОНЕЦ ФАЙЛА, ПОСЛЕ ВСЕГО ---

# Роут для генерации Crypto-инвойса
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

# Роут для вебхука CryptoBot
@app.route('/api/crypto-webhook', methods=['POST'])
def crypto_webhook():
    update = request.get_json()
    
    if update.get('update_type') == 'invoice_paid':
        payload = update['payload']
        user_id = str(payload['payload'])
        amount_ton = float(payload['asset_pay_amount'])
        balance_to_add = int(amount_ton * 100) # Твой коэффициент
        
        if supabase:
            try:
                res = supabase.table("users").select("balance").eq("user_id", user_id).execute()
                if res.data:
                    current_bal = res.data[0].get('balance', 0) or 0
                    supabase.table("users").update({"balance": current_bal + balance_to_add}).eq("user_id", user_id).execute()
                else:
                    supabase.table("users").insert({"user_id": user_id, "balance": balance_to_add}).execute()
            except Exception as e:
                print(f"Crypto DB Error: {e}")
                
    return "OK", 200
