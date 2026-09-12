import os
import random
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client

app = Flask(__name__)
# Включаем CORS глобально
CORS(app, resources={r"/api/*": {"origins": "*"}, r"/webhook": {"origins": "*"}, r"/api/crypto-webhook": {"origins": "*"}})

# Инициализация
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
CRYPTO_TOKEN = os.environ.get("CRYPTO_PAY_TOKEN")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

# Стартовый бонус звёзд при регистрации через /start. Это ваша внутренняя
# валюта (колонка stars в таблице users), НЕ настоящие Telegram Stars —
# поэтому тут можно смело ставить дробное число вроде 0.001, если хочется.
WELCOME_BONUS_STARS = float(os.environ.get("WELCOME_BONUS_STARS", "1"))

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


def find_user_by_id(table_select, uid_str):
    """
    Универсальный поиск пользователя: сначала пробуем как число (int8 колонка),
    затем как строку. Возвращает (query_id, user_data) или (query_id, None).
    """
    query_id = int(uid_str) if str(uid_str).isdigit() else uid_str
    res = supabase.table("users").select(table_select).eq("user_id", query_id).execute()

    if not res.data and query_id != str(uid_str):
        res = supabase.table("users").select(table_select).eq("user_id", str(uid_str)).execute()
        if res.data:
            query_id = str(uid_str)

    user_data = res.data[0] if res.data else None
    return query_id, user_data


def build_default_user_payload(query_id, tg_from):
    """
    Полный набор полей, которые ожидают увидеть разные страницы приложения
    (profile.html, index.html, swap, rolls и т.д.). Тут это единственное
    место, где реально создаётся пользователь — через service_role ключ,
    который полностью игнорирует RLS, поэтому регистрация не зависит от
    того, как настроены политики на таблице users.
    """
    return {
        "user_id": query_id,
        "username": tg_from.get("username"),
        "first_name": tg_from.get("first_name") or "ИГРОК",
        "stars": WELCOME_BONUS_STARS,
        "balance": 0,
        "tickets": 0,
        "inventory": [],
        "referral_count": 0,
        "spin_count": 0,
        "last_free_spin": None,
        "used_promos": None,
        "has_used_referral": False,
        "activated_referral_code": None
    }


def register_user_if_new(tg_from):
    """
    Регистрирует пользователя при первом /start. Если пользователь уже
    существует — ничего не трогает (баланс не обнуляется повторным /start).
    Возвращает (user_data, is_new).
    """
    uid_str = str(tg_from.get("id"))
    query_id = int(uid_str) if uid_str.isdigit() else uid_str

    query_id, existing = find_user_by_id("*", uid_str)
    if existing:
        return existing, False

    payload = build_default_user_payload(query_id, tg_from)
    try:
        res = supabase.table("users").insert(payload).execute()
        if res.data:
            print(f"SUCCESS: registered new user {uid_str} via /start, bonus={WELCOME_BONUS_STARS}")
            return res.data[0], True
    except Exception as e:
        # Могла случиться гонка (юзер уже создан параллельным запросом) —
        # перечитываем строку ещё раз перед тем как сдаться.
        print(f"WARNING: insert on /start failed for {uid_str}: {e}")
        query_id, reread = find_user_by_id("*", uid_str)
        if reread:
            return reread, False

    return None, False


def handle_start_referral(new_user_id, start_param):
    """
    Серверная версия handleReferral() из index.html. Дублирует клиентскую
    логику, но идёт через service_role — гарантированно не спотыкается о
    RLS. Если обе версии сработают на одном и том же реферале, повторной
    вставки не будет благодаря проверке on existing referral row ниже —
    так что держать обе безопасно, но после того как этот эндпоинт
    подтвердит стабильную работу, клиентский handleReferral в index.html
    можно смело убрать.
    """
    if not start_param or str(start_param) == str(new_user_id):
        return

    try:
        existing = supabase.table("referrals").select("id").eq("referred_id", str(new_user_id)).maybe_single().execute()
        if existing and existing.data:
            return  # уже засчитан реферал для этого юзера

        supabase.table("referrals").insert({
            "referrer_id": str(start_param),
            "referred_id": str(new_user_id),
            "claimed": False
        }).execute()

        supabase.rpc("increment_tickets", {
            "target_user_id": str(start_param),
            "amount": 1
        }).execute()

        print(f"SUCCESS: referral counted, referrer={start_param}, referred={new_user_id}")
    except Exception as e:
        print(f"WARNING: referral handling failed: {e}")


@app.route('/api/get_inventory', methods=['GET', 'OPTIONS'])
def get_inventory():
    if request.method == 'OPTIONS':
        return '', 200

    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "No user_id provided"}), 400

    try:
        query_id, user_data = find_user_by_id("inventory", user_id)

        if user_data:
            raw_inventory = user_data.get("inventory", [])
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

        query_id, user_data = find_user_by_id("inventory", user_id)

        if not user_data:
            return jsonify({"error": "Пользователь не найден."}), 404

        current_inventory = user_data.get("inventory", [])
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
    data = request.get_json() or {}
    uid = str(data.get('user_id'))
    item_name = data.get('item_name')

    user_res = supabase.table("users").select("stars, inventory").eq("user_id", uid).single().execute()
    user = user_res.data

    if not user:
        return jsonify({"success": False, "error": "Пользователь не найден"}), 404

    current_stars = float(user.get('stars', 0))
    inventory = user.get('inventory', [])

    if current_stars < 75:
        return jsonify({"success": False, "error": "Недостаточно звезд"}), 400

    if item_name not in inventory:
        return jsonify({"success": False, "error": "Предмет не найден в инвентаре"}), 400

    try:
        unique_payload = f"verify_{uid}_{item_name}_{int(time.time())}"

        tg_payload = {
            "title": "NowearSpin",
            "description": f"Верификация вывода предмета: {item_name}",
            "payload": unique_payload,
            "currency": "XTR",
            "prices": [{"label": "Verification", "amount": 5}]
        }

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/createInvoiceLink"
        r = requests.post(url, json=tg_payload, timeout=10)
        resp = r.json()

        if resp.get('ok'):
            return jsonify({"success": True, "pay_url": resp['result']}), 200

        return jsonify({"success": False, "error": "Не удалось создать инвойс верификации"}), 400

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"success": False, "error": "Ошибка сервера"}), 500


@app.route('/api/create_stars_pay', methods=['POST'])
def create_stars_pay():
    data = request.get_json() or {}
    uid = str(data.get('user_id', '0'))
    gift_name = data.get('gift_name', 'unknown')
    try:
        amount = int(data.get('amount', 0))
    except:
        amount = 0

    if amount < 1:
        return jsonify({"error": "Сумма пополнения должна быть больше 0"}), 400

    unique_payload = f"stars_{uid}_{amount}_{int(time.time())}"

    tg_payload = {
        "title": "NowearSpin",
        "description": f"Пополнение баланса: {amount} звезд",
        "payload": unique_payload,
        "currency": "XTR",
        "prices": [{"label": "Stars", "amount": amount}]
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

        # 0. /start — регистрация пользователя и учёт реферала.
        #    Это единственное надёжное место для создания юзера: работает
        #    через service_role ключ, который полностью игнорирует RLS,
        #    и срабатывает ДО того, как человек вообще откроет вебапп.
        if 'message' in update and 'text' in update['message']:
            msg = update['message']
            text = msg.get('text', '') or ''

            if text.startswith('/start'):
                tg_from = msg.get('from', {}) or {}
                if tg_from.get('id'):
                    user_data, is_new = register_user_if_new(tg_from)

                    parts = text.split(maxsplit=1)
                    start_param = parts[1].strip() if len(parts) > 1 else None

                    if is_new and start_param:
                        handle_start_referral(str(tg_from['id']), start_param)

                    if is_new:
                        try:
                            bonus_text = f"{WELCOME_BONUS_STARS:g}"
                            requests.post(
                                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                                json={
                                    "chat_id": msg['chat']['id'],
                                    "text": f"Добро пожаловать в NowearSpin! Начислили {bonus_text} ⭐ на баланс."
                                },
                                timeout=HTTP_TIMEOUT
                            )
                        except Exception as e:
                            print(f"WARNING: welcome message failed: {e}")

                return "OK", 200

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

            # Обработка верификации вывода предмета
            if payload.startswith("verify_"):
                uid_str = parts[1]
                item_name = parts[2]

                query_id, user_data = find_user_by_id("inventory", uid_str)

                if not user_data:
                    print(f"WARNING: withdrawal verify — user {uid_str} not found in DB")
                    return "OK", 200

                inv = user_data.get('inventory', []) or []
                if isinstance(inv, list) and item_name in inv:
                    inv.remove(item_name)

                    supabase.table("orders").insert({
                        "user_id": uid_str,
                        "item_name": item_name,
                        "item_img": f"{item_name}.png",
                        "status": "pending"
                    }).execute()

                    supabase.table("users").update({
                        "inventory": inv
                    }).eq("user_id", query_id).execute()

                    print(f"SUCCESS: Withdrawal verified for User {uid_str}, item: {item_name}")
                else:
                    print(f"WARNING: item {item_name} not found in inventory of user {uid_str}")

                return "OK", 200

            # Обработка обычного пополнения звёзд
            elif payload.startswith("stars_"):
                uid_str = parts[1]
                amount = int(parts[2])

                query_id, user_data = find_user_by_id("stars", uid_str)

                if not user_data:
                    print(f"WARNING: stars topup — user {uid_str} not found in DB, payload={payload}")
                    return "OK", 200

                current_stars = float(user_data.get('stars', 0) or 0)
                supabase.table("users").update({
                    "stars": current_stars + amount,
                    "is_paid_75": True
                }).eq("user_id", query_id).execute()

                print(f"SUCCESS: User {uid_str} topped up stars. Amount: {amount}. New balance: {current_stars + amount}")
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

        query_id, user_data = find_user_by_id("balance", user_id)

        if user_data:
            old_bal = float(user_data.get('balance') or 0)
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
