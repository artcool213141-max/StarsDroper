import os
import random
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS  # Нужен для надежной работы CORS при ошибках 500/400
from supabase import create_client
 
app = Flask(__name__)
# Включаем CORS глобально, чтобы браузер не ругался при ошибках
CORS(app, resources={r"/api/*": {"origins": "*"}, r"/webhook": {"origins": "*"}, r"/api/crypto-webhook": {"origins": "*"}})
 
# Инициализация
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
CRYPTO_TOKEN = os.environ.get("CRYPTO_PAY_TOKEN")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None
 
HTTP_TIMEOUT = 10
 
# Публичный адрес бэкенда — используется для автонастройки вебхука
BACKEND_PUBLIC_URL = "https://stars-droper-main.vercel.app"
 
giftDatabase = {
    "1may.jpg": {"price": 100}, "1may.png": {"price": 100}, "chassiki.png": {"price": 4700},
    "sliva.png": {"price": 33500}, "soska.png": {"price": 2500}, "zirka.png": {"price": 850},
    "2025.jpg": {"price": 500}, "bear.png": {"price": 3500}, "book.jpg": {"price": 1000},
    "booox.png": {"price": 700}, "botinok.png": {"price": 400}, "box.png": {"price": 600},
    "car.png": {"price": 5000}, "raketa.png": {"price": 50}, "ccolso2.png": {"price": 3000},
    "cerrrdce.jpg": {"price": 500}, "chemodan.jpg": {"price": 5000}, "ciga.png": {"price": 3000},
    "colso.png": {"price": 2500}, "costum.jpg": {"price": 10000}, "cvetok.png": {"price": 1000},
    "dog.png": {"price": 500}, "dyxi.png": {"price": 10000}, "fonarik.jpg": {"price": 100},
    "grob.jpg": {"price": 5000}, "gyba.png": {"price": 5000}, "happybirthday.jpg": {"price": 200},
    "heart.png": {"price": 2000}, "helmet.png": {"price": 25000}, "kalendar.png": {"price": 400},
    "kepka.png": {"price": 100000}, "kirpitch.jpg": {"price": 10000}, "koks.jpg": {"price": 150},
    "koktel.png": {"price": 500}, "kot.png": {"price": 10000}, "kotel.png": {"price": 500},
    "krovatka.jpg": {"price": 600}, "lolipop.png": {"price": 500}, "lucky.jpg": {"price": 500},
    "mafin.jpg": {"price": 700}, "metch.png": {"price": 700}, "narkotiki.png": {"price": 700},
    "obyv.jpg": {"price": 10000}, "orel.jpg": {"price": 5000}, "otkritka.jpg": {"price": 150},
    "paska.jpg": {"price": 75}, "rozza.png": {"price": 2000}, "rykzak.jpg": {"price": 500},
    "shapka.png": {"price": 500}, "shar.jpg": {"price": 1000}, "shlem.png": {"price": 3500},
    "soska.jpg": {"price": 3000}, "star.png": {"price": 5}, "statyya.jpg": {"price": 41000},
    "venok.png": {"price": 500}, "yayko.png": {"price": 600}, "zhele.png": {"price": 700},
    "zmei.png": {"price": 500}, "meczcc.png": {"price": 600}, "kryg.PNG": {"price": 600},
    "gribb.PNG": {"price": 600}, "zirka.PNG": {"price": 800}, "cvetk.PNG": {"price": 900},
    "sshapka.PNG": {"price": 2300}, "tyfli.PNG": {"price": 1800}
}
 
 
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response
 
 
@app.route('/api/get_inventory', methods=['GET', 'OPTIONS'])
def get_inventory():
    if request.method == 'OPTIONS':
        return '', 200
 
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "No user_id provided"}), 400
 
    try:
        query_id = int(user_id) if user_id.isdigit() else user_id
        res = supabase.table("users").select("inventory").eq("user_id", query_id).execute()
 
        if not res.data:
            res = supabase.table("users").select("inventory").eq("user_id", str(user_id)).execute()
 
        if res.data:
            raw_inventory = res.data[0].get("inventory", [])
            if not isinstance(raw_inventory, list):
                raw_inventory = []
 
            cleaned_string_inventory = []
            has_bad_data = False
 
            for item in raw_inventory:
                if isinstance(item, str):
                    clean_name = item.replace("img/", "")
                    cleaned_string_inventory.append(clean_name)
                elif isinstance(item, dict):
                    img_path = item.get("img", "star.png")
                    clean_name = img_path.replace("img/", "")
                    cleaned_string_inventory.append(clean_name)
                    has_bad_data = True
 
            if has_bad_data:
                try:
                    supabase.table("users").update({"inventory": cleaned_string_inventory}).eq("user_id", query_id).execute()
                except Exception:
                    pass
 
            return jsonify({"success": True, "inventory": cleaned_string_inventory}), 200
 
        return jsonify({"success": True, "inventory": []}), 200
    except Exception as e:
        return jsonify({"error": "Server error", "details": str(e)}), 500
 
 
@app.route('/api/craft_gift', methods=['POST', 'OPTIONS'])
def craft_gift():
    if request.method == 'OPTIONS':
        return '', 200
 
    data = request.get_json() or {}
    user_id = data.get('user_id')
    gift_keys = data.get('gift_keys', [])
 
    if not user_id or not gift_keys or len(gift_keys) != 5:
        return jsonify({"error": "Передайте ровно 5 предметов."}), 400
 
    try:
        total_price = 0
        for key in gift_keys:
            clean_key = key.replace("img/", "")
            if clean_key not in giftDatabase:
                return jsonify({"error": f"Предмет {clean_key} не найден."}), 400
            total_price += giftDatabase[clean_key]["price"]
 
        query_id = int(user_id) if str(user_id).isdigit() else user_id
        res = supabase.table("users").select("inventory").eq("user_id", query_id).execute()
 
        if not res.data:
            res = supabase.table("users").select("inventory").eq("user_id", str(user_id)).execute()
 
        if not res.data:
            return jsonify({"error": "Пользователь не найден."}), 404
 
        current_inventory = res.data[0].get("inventory", [])
        if not isinstance(current_inventory, list):
            current_inventory = []
 
        current_inventory = [item.replace("img/", "") if isinstance(item, str) else item for item in current_inventory]
 
        for key in gift_keys:
            clean_key = key.replace("img/", "")
            if clean_key in current_inventory:
                current_inventory.remove(clean_key)
 
        rand = random.random() * 100
        pool = []
 
        if rand <= 30:
            pool = [k for k, v in giftDatabase.items() if total_price * 0.1 <= v["price"] <= total_price * 0.6]
        elif rand <= 70:
            pool = [k for k, v in giftDatabase.items() if total_price * 0.8 <= v["price"] <= total_price * 1.2]
        else:
            pool = [k for k, v in giftDatabase.items() if total_price * 1.3 <= v["price"] <= total_price * 2.5]
 
        if not pool:
            pool = list(giftDatabase.keys())
 
        win_key = random.choice(pool)
        current_inventory.append(win_key)
 
        supabase.table("users").update({"inventory": current_inventory}).eq("user_id", query_id).execute()
        return jsonify({"success": True, "new_gift_key": win_key}), 200
 
    except Exception as e:
        return jsonify({"error": "Ошибка сервера при крафте", "details": str(e)}), 500

@app.route('/api/process_withdrawal', methods=['POST'])
def process_withdrawal():
    data = request.get_json()
    uid = str(data.get('user_id'))
    item_name = data.get('item_name') # Это точное имя гифта из инвентаря
    
    # 1. Получаем текущие данные пользователя из Supabase
    user_res = supabase.table("users").select("stars, inventory").eq("user_id", uid).single().execute()
    user = user_res.data
    
    if not user:
        return jsonify({"success": False, "error": "Пользователь не найден"}), 404
        
    current_stars = float(user.get('stars', 0))
    inventory = user.get('inventory', [])
    
    # 2. Валидация
    if current_stars < 75:
        return jsonify({"success": False, "error": "Недостаточно звезд"}), 400
    
    if item_name not in inventory:
        return jsonify({"success": False, "error": "Предмет не найден в инвентаре"}), 400

    # 3. Транзакция: обновляем пользователя и создаем заказ
    try:
        # Списываем звезды и удаляем предмет из массива
        new_inventory = inventory.copy()
        new_inventory.remove(item_name)
        
        supabase.table("users").update({
            "stars": current_stars - 75,
            "inventory": new_inventory
        }).eq("user_id", uid).execute()
        
        # Создаем запись в orders (согласно твоей структуре таблицы)
        supabase.table("orders").insert({
            "user_id": uid,
            "item_name": item_name,
            "item_img": f"{item_name}.png", # Убедись, что файлы называются так
            "status": "pending"
        }).execute()
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"success": False, "error": "Ошибка базы данных"}), 500
 
 
@app.route('/api/create_stars_pay', methods=['POST'])
def create_stars_pay():
    import time
    
    data = request.get_json() or {}
    uid = str(data.get('user_id', '0'))
    gift_name = data.get('gift_name', 'unknown')
    try:
        amount = int(data.get('amount', 0))
    except:
        amount = 0

    if amount < 1:
        return jsonify({"error": "Invalid amount"}), 400

    # запоминаем, какой именно предмет юзер сейчас пытается вывести
    supabase.table('users').update({'pending_item': gift_name}).eq('user_id', uid).execute()

    unique_payload = f"stars_{uid}_{amount}_{int(time.time())}"
    
    tg_payload = {
        "title": "NowearSpin Withdrawal",
        "description": f"Верификация для вывода: {gift_name}",
        "payload": unique_payload,
        "provider_token": "",
        "currency": "XTR",
        "prices": [{"label": "Verification", "amount": amount}]
    }

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/createInvoiceLink"

    try:
        r = requests.post(url, json=tg_payload, timeout=10)
        resp = r.json()
    except Exception as e:
        return jsonify({"error": "Request failed", "details": str(e)}), 500
    
    if resp.get('ok'):
        return jsonify({"pay_url": resp['result']}), 200
    
    return jsonify(resp), 400
 
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = request.get_json() or {}

        # 1. PreCheckout
        if 'pre_checkout_query' in update:
            query_id = update['pre_checkout_query']['id']
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery",
                          json={"pre_checkout_query_id": query_id, "ok": True}, timeout=10)
            return "OK", 200

        # 2. Успешный платеж
        if 'message' in update and 'successful_payment' in update['message']:
            payment = update['message']['successful_payment']
            user_id = str(update['message']['from']['id'])
            payload = payment.get('invoice_payload', "")

            parts = payload.split('_')
            uid_str = parts[1]
            amount = int(parts[2])

            user_response = supabase.table("users").select("stars, inventory, pending_item").eq("user_id", uid_str).execute()
            user_data = user_response.data[0] if user_response.data else None

            if not user_data:
                return "OK", 200

            if amount == 1:
                # ТЕСТ: 1 ⭐ вместо 30 — верификационный платёж за вывод подарка
                pending_item = user_data.get('pending_item')
                inv = user_data.get('inventory', []) or []

                if pending_item and isinstance(inv, list):
                    new_inv = []
                    removed = False
                    for item in inv:
                        if not removed and item == pending_item:
                            removed = True
                            continue
                        new_inv.append(item)

                    if removed:
                        supabase.table("orders").insert({
                            "user_id": uid_str,
                            "item_name": pending_item,
                            "item_img": f"{pending_item}",
                            "status": "pending"
                        }).execute()

                        supabase.table("users").update({
                            "inventory": new_inv,
                            "pending_item": None
                        }).eq("user_id", uid_str).execute()
            else:
                # обычное пополнение внутреннего баланса звёзд
                supabase.table("users").update({
                    "stars": float(user_data.get('stars', 0)) + amount,
                    "is_paid_75": True
                }).eq("user_id", uid_str).execute()

                credit_ambassador_commission(uid_str, amount, source="stars")

            print(f"SUCCESS: User {uid_str} processed. Amount: {amount}")
            return "OK", 200

        return "OK", 200
    except Exception as e:
        print(f"CRITICAL WEBHOOK ERROR: {str(e)}")
        return "OK", 200
     
 
@app.route('/api/create_crypto_pay', methods=['POST'])
def create_crypto_pay():
    data = request.get_json() or {}
    uid = str(data.get('user_id'))
    amount = float(data.get('amount'))
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    payload = {"asset": "TON", "amount": str(amount), "payload": uid}
    try:
        r = requests.post("https://pay.crypt.bot/api/createInvoice", json=payload, headers=headers, timeout=HTTP_TIMEOUT)
        resp = r.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "CryptoBot API недоступен", "details": str(e)}), 502
 
    if resp.get('ok'):
        return jsonify({"pay_url": resp['result']['pay_url']}), 200
    return jsonify(resp), 400
 
 
@app.route('/api/crypto-webhook', methods=['POST', 'GET'])
def crypto_webhook():
    if request.method == 'GET':
        return "Webhook is active!", 200
 
    data = request.get_json() or {}
    if data.get('update_type') != 'invoice_paid':
        return "OK", 200
 
    try:
        payload_data = data.get('payload', {})
        user_id = str(payload_data.get('payload'))
        amount_ton = float(payload_data.get('asset_pay_amount') or payload_data.get('amount') or 0)
 
        if not user_id or user_id == "None":
            print("ERROR: Crypto Webhook received empty user_id")
            return "OK", 200
 
        query_id = int(user_id) if user_id.isdigit() else user_id
        res = supabase.table("users").select("balance").eq("user_id", query_id).execute()
 
        if res.data and len(res.data) > 0:
            old_bal = float(res.data[0].get('balance') or 0)
            new_bal = old_bal + amount_ton
            supabase.table("users").update({"balance": new_bal}).eq("user_id", query_id).execute()
        else:
            supabase.table("users").insert({"user_id": user_id, "balance": amount_ton}).execute()
 
        return "OK", 200
    except Exception as e:
        print(f"CRITICAL CRYPTO WEBHOOK ERROR: {str(e)}")
        return "OK", 200
 
 
@app.route('/api/ensure_webhook', methods=['GET'])
def ensure_webhook():
    """
    Принудительно переустанавливает вебхук с правильным набором allowed_updates.
 
    Открой https://<твой-бэкенд>/api/ensure_webhook в браузере ОДИН РАЗ (и после
    любого случайного вызова голого setWebhook без allowed_updates), чтобы
    гарантированно подписаться на pre_checkout_query — без него Telegram
    не присылает запрос на подтверждение Stars-оплаты, и кнопка
    "Confirm and Pay" висит бесконечно.
    """
    if not BOT_TOKEN:
        return jsonify({"error": "Нет BOT_TOKEN в переменных окружения"}), 500
 
    webhook_url = f"{BACKEND_PUBLIC_URL}/webhook"
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            json={
                "url": webhook_url,
                "allowed_updates": ["message", "pre_checkout_query"]
            },
            timeout=HTTP_TIMEOUT
        )
        result = r.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Telegram API недоступен", "details": str(e)}), 502
 
    # Сразу же подтягиваем актуальный статус, чтобы видно было allowed_updates
    try:
        info = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo",
            timeout=HTTP_TIMEOUT
        ).json()
    except requests.exceptions.RequestException:
        info = None
 
    return jsonify({"set_webhook_result": result, "webhook_info": info}), 200
 
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
