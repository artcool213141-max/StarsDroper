import os, requests
from flask import Flask, request, jsonify
from supabase import create_client

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/api/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    
    # 1. Отвечаем на Pre-checkout (обязательно в течение 10 сек)
    if 'pre_checkout_query' in update:
        query_id = update['pre_checkout_query']['id']
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery", 
                      json={"pre_checkout_query_id": query_id, "ok": True})
        return "OK", 200

    # 2. Обработка успешного платежа и запись в базу
    if 'message' in update and 'successful_payment' in update['message']:
        payment = update['message']['successful_payment']
        user_id = update['message']['from']['id'] # Telegram ID плательщика
        amount = payment['total_amount'] # Количество звезд
        charge_id = payment['telegram_payment_charge_id']
        
        # Пишем в Supabase
        # Предполагаем, что у тебя таблица называется 'payments'
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
def crypto_webhook():
    return "OK", 200

@app.route('/api/stars-webhook', methods=['POST'])
def stars_webhook():
    return "OK", 200

if __name__ == '__main__':
    app.run()
