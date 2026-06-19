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
    
    # 1. Обработка pre_checkout_query (оставляем)
    if 'pre_checkout_query' in update:
        query_id = update['pre_checkout_query']['id']
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery", 
                      json={"pre_checkout_query_id": query_id, "ok": True})
        return "OK", 200

    # 2. Обработка УСПЕШНОЙ ОПЛАТЫ
    if 'message' in update and 'successful_payment' in update['message']:
        user_id = str(update['message']['from']['id'])
        
        # ДИАГНОСТИКА: Печатаем прямо в логи
        print(f"--- WEBHOOK START: User {user_id} ---")
        
        # Получаем данные
        res = supabase.table("users").select("*").eq("user_id", user_id).execute()
        
        if not res.data:
            print(f"ERROR: Пользователь {user_id} не найден в базе!")
            return "OK", 200
        
        user_data = res.data[0]
        print(f"DEBUG: Пользователь найден. Stars: {user_data.get('stars')}, Pending: {user_data.get('pending_item')}")
        
        # ВЫПОЛНЯЕМ ОБНОВЛЕНИЕ
        try:
            # Обновляем пользователя
            supabase.table("users").update({
                "is_paid_75": True,
                "stars": (user_data.get('stars') or 0) + 1, # пример
                "pending_item": None,
                "inventory": [] # Проверим, удалится ли хотя бы это
            }).eq("user_id", user_id).execute()
            print("SUCCESS: Пользователь обновлен")

            # Вставляем в orders (принудительно)
            supabase.table("orders").insert({
                "user_id": user_id,
                "item_name": "Gift",
                "status": "pending"
            }).execute()
            print("SUCCESS: Запись в orders создана")
            
        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}")
            
    return "OK", 200
    
@app.route('/api/create_order', methods=['POST'])
def create_order():
    data = request.get_json()
    user_id = str(data.get('user_id'))
    try:
        # Вставляем данные. Если есть ошибка, мы ее увидим в консоли
        response = supabase.table("orders").insert({
            "user_id": user_id,
            "item_name": data.get('item_name'),
            "item_img": data.get('item_img'),
            "status": "pending"
        }).execute()
        
        print(f"DEBUG: Заявка создана для {user_id}")
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"CRITICAL ERROR (create_order): {str(e)}") # Вот это покажет причину
        return jsonify({"status": "error", "message": str(e)}), 400

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
