import os
import requests

from flask import Flask, request, jsonify
from supabase import create_client

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
CRYPTO_TOKEN = os.getenv("CRYPTO_PAY_TOKEN")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not found")

if not SUPABASE_URL:
    raise Exception("SUPABASE_URL not found")

if not SUPABASE_KEY:
    raise Exception("SUPABASE_SERVICE_ROLE_KEY not found")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# =========================
# TELEGRAM STARS
# =========================

@app.route("/api/create_stars_pay", methods=["POST"])
def create_stars_pay():

    try:
        data = request.get_json(force=True)

        user_id = str(data.get("user_id"))
        amount = int(data.get("amount", 1))

        payload = {
            "title": "Stars Topup",
            "description": f"Пополнение на {amount} Stars",
            "payload": f"uid_{user_id}",
            "currency": "XTR",
            "prices": [
                {
                    "label": "Stars",
                    "amount": amount
                }
            ]
        }

        telegram_url = (
            f"https://api.telegram.org/bot{BOT_TOKEN}/createInvoiceLink"
        )

        r = requests.post(
            telegram_url,
            json=payload,
            timeout=15
        )

        resp = r.json()

        print("TELEGRAM RESPONSE:", resp)

        if not resp.get("ok"):
            return jsonify(resp), 400

        return jsonify({
            "success": True,
            "pay_url": resp["result"]
        })

    except Exception as e:
        print("STARS ERROR:", str(e))
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================
# TELEGRAM WEBHOOK
# =========================

@app.route("/api/webhook", methods=["POST"])
def webhook():

    try:
        update = request.get_json(force=True)

        print("WEBHOOK UPDATE:", update)

        message = update.get("message")

        if not message:
            return "OK", 200

        successful_payment = message.get("successful_payment")

        if not successful_payment:
            return "OK", 200

        user_id = str(message["from"]["id"])

        stars_paid = int(
            successful_payment.get("total_amount", 0)
        )

        verification_payment = stars_paid == 1

        user_row = (
            supabase
            .table("users")
            .select("*")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )

        current_stars = 0
        current_paid = False

        if user_row.data:
            current_stars = user_row.data.get("stars", 0)
            current_paid = user_row.data.get(
                "is_paid_75",
                False
            )

        supabase.table("users").upsert({
            "user_id": user_id,
            "stars": current_stars + stars_paid,
            "is_paid_75": current_paid or verification_payment
        }).execute()

        print(
            f"Stars credited: {user_id} +{stars_paid}"
        )

        return "OK", 200

    except Exception as e:
        print("WEBHOOK ERROR:", str(e))
        return "OK", 200


# =========================
# CRYPTOBOT
# =========================

@app.route("/api/create_crypto_pay", methods=["POST"])
def create_crypto_pay():

    try:
        data = request.get_json(force=True)

        user_id = str(data.get("user_id"))
        amount = float(data.get("amount"))

        headers = {
            "Crypto-Pay-API-Token": CRYPTO_TOKEN
        }

        payload = {
            "asset": "TON",
            "amount": str(amount),
            "payload": user_id
        }

        r = requests.post(
            "https://pay.crypt.bot/api/createInvoice",
            json=payload,
            headers=headers,
            timeout=15
        )

        resp = r.json()

        print("CRYPTO RESPONSE:", resp)

        if not resp.get("ok"):
            return jsonify(resp), 400

        return jsonify({
            "success": True,
            "pay_url": resp["result"]["pay_url"]
        })

    except Exception as e:
        print("CRYPTO ERROR:", str(e))

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================
# CRYPTO WEBHOOK
# =========================

@app.route("/api/crypto-webhook", methods=["GET", "POST"])
def crypto_webhook():

    if request.method == "GET":
        return "Webhook active", 200

    try:
        data = request.get_json(force=True)

        print("CRYPTO WEBHOOK:", data)

        if data.get("update_type") != "invoice_paid":
            return "OK", 200

        payload = data.get("payload", {})

        user_id = str(
            payload.get("payload")
        )

        amount_ton = float(
            payload.get("asset_pay_amount")
            or payload.get("amount")
            or 0
        )

        user_row = (
            supabase
            .table("users")
            .select("balance")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )

        old_balance = 0

        if user_row.data:
            old_balance = float(
                user_row.data.get("balance", 0)
            )

        new_balance = old_balance + amount_ton

        supabase.table("users").upsert({
            "user_id": user_id,
            "balance": new_balance
        }).execute()

        print(
            f"Balance credited: {user_id} +{amount_ton} TON"
        )

        return "OK", 200

    except Exception as e:
        print("CRYPTO WEBHOOK ERROR:", str(e))
        return "OK", 200


@app.route("/")
def health():
    return {
        "status": "ok"
    }


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000))
    )
