import os
import random
import requests
from flask import Flask, request, jsonify
from supabase import create_client

app = Flask(__name__)

# Инициализация
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
CRYPTO_TOKEN = os.environ.get("CRYPTO_PAY_TOKEN")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

# База данных подарков для крафта
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

# Настройка CORS глобально для всех ответов Flask
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

# --- ПОЛУЧЕНИЕ ИНВЕНТАРЯ ---
# --- ПОЛУЧЕНИЕ ИНВЕНТАРЯ (СТРОГИЙ СТРИНГ-РЕЖИМ) ---
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
                    # Если в базе лежит полный путь типа "img/soska.jpg", убираем префикс, 
                    # потому что твой фронтенд сам добавляет IMAGE_FOLDER ('img/')
                    clean_name = item.replace("img/", "")
                    cleaned_string_inventory.append(clean_name)
                elif isinstance(item, dict):
                    # Если в базу закрался объект, вытаскиваем из него только имя файла
                    img_path = item.get("img", "star.png")
                    clean_name = img_path.replace("img/", "")
                    cleaned_string_inventory.append(clean_name)
                    has_bad_data = True  # Заметили грязь в базе

            # Если в базе был мусор из объектов, автоматически перезаписываем её чистыми строками
            if has_bad_data:
                try:
                    supabase.table("users").update({"inventory": cleaned_string_inventory}).eq("user_id", query_id).execute()
                except Exception:
                    pass

            return jsonify({"success": True, "inventory": cleaned_string_inventory}), 200
            
        return jsonify({"success": True, "inventory": []}), 200
    except Exception as e:
        return jsonify({"error": "Server error", "details": str(e)}), 500

# --- КРАФТ ПОДАРКА ---
# --- КРАФТ ПОДАРКА (БЕЗ ЖЕСТКОЙ БЛОКИРОВКИ ПОВТОРОВ) ---
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
            # На всякий случай очищаем ключи от "img/", если фронт их пришлет с префиксом
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

        # Очищаем инвентарь из базы от путей "img/", чтобы было точное совпадение строк
        current_inventory = [item.replace("img/", "") if isinstance(item, str) else item for item in current_inventory]

        # Мягкое списание: удаляем из инвентаря только то, что там реально нашлось
        for key in gift_keys:
            clean_key = key.replace("img/", "")
            if clean_key in current_inventory:
                current_inventory.remove(clean_key)
        
        # Рассчитываем выигрыш
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

        # Сохраняем обновленный инвентарь обратно в базу
        supabase.table("users").update({"inventory": current_inventory}).eq("user_id", query_id).execute()
        return jsonify({"success": True, "new_gift_key": win_key}), 200

    except Exception as e:
        return jsonify({"error": "Ошибка сервера при крафте", "details": str(e)}), 500
        
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
    
    if 'pre_checkout_query' in update:
        query_id = update['pre_checkout_query']['id']
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery", 
                      json={"pre_checkout_query_id": query_id, "ok": True})
        return "OK", 200

    if 'message' in update and 'successful_payment' in update['message']:
        user_id = str(update['message']['from']['id'])
        print(f"--- WEBHOOK START: User {user_id} ---")
        
        query_id = int(user_id) if user_id.isdigit() else user_id
        res = supabase.table("users").select("*").eq("user_id", query_id).execute()
        
        if not res.data:
            print(f"ERROR: Пользователь {user_id} не найден в базе!")
            return "OK", 200
        
        user_data = res.data[0]
        
        try:
            supabase.table("users").update({
                "is_paid_75": True,
                "stars": (user_data.get('stars') or 0) + 1,
                "pending_item": None,
                "inventory": []
            }).eq("user_id", query_id).execute()
            print("SUCCESS: Пользователь обновлен")

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
        supabase.table("orders").insert({
            "user_id": user_id,
            "item_name": data.get('item_name'),
            "item_img": data.get('item_img'),
            "status": "pending"
        }).execute()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

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
    if data.get('update_type') != 'invoice_paid':
        return "OK", 200

    try:
        payload = data.get('payload', {})
        user_id = str(payload.get('payload'))
        amount_ton = float(payload.get('asset_pay_amount') or payload.get('amount') or 0)
        
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
        print(f"CRITICAL ERROR: {str(e)}") 
        return "OK", 200
