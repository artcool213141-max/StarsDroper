"""
Роутер ивента «Кровавая Жатва» — версия для Flask (Blueprint).

Подключение в основном файле (см. инструкцию в чате):
    from event_api import bp as event_bp
    app.register_blueprint(event_bp)

Используются те же переменные окружения, что у основного бэкенда:
    BOT_TOKEN, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
Новых pip-пакетов не нужно (supabase и flask уже есть).
"""
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl

from flask import Blueprint, jsonify, request
from supabase import create_client

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])

bp = Blueprint("event", __name__, url_prefix="/event")

# Только для показа в интерфейсе. Реальные значения живут в SQL-функциях —
# если меняешь экономику, меняй и там, и тут.
CFG = {
    "harvest_cooldown": 3600,
    "harvest_min": 5,
    "harvest_max": 10,
    "shield_cost": 50,
    "shield_hours": 12,
    "shield_max_hours": 24,
    "shield_block": 50,
    "soul_per_star": 1000,
    "daily_star_cap": 3,
    "min_souls_battle": 10,
    "round_seconds": 12,
    "steal_percent": 15,
}


class ApiError(Exception):
    def __init__(self, status, detail):
        self.status = status
        self.detail = detail


@bp.errorhandler(ApiError)
def handle_api_error(e):
    return jsonify({"detail": e.detail}), e.status


def body():
    return request.get_json(silent=True) or {}


# ---------- авторизация через Telegram initData ----------
def auth(data):
    init_data = data.get("init_data")
    if not init_data:
        raise ApiError(401, "no init_data")
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received = pairs.pop("hash", None)
    if not received:
        raise ApiError(401, "no hash")

    check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc, received):
        raise ApiError(401, "bad signature")
    try:
        age = time.time() - int(pairs.get("auth_date", "0"))
    except ValueError:
        raise ApiError(401, "bad auth_date")
    if age > 86400:
        raise ApiError(401, "init_data expired")

    try:
        user = json.loads(pairs["user"])
    except Exception:
        raise ApiError(401, "no user")
    name = ("@" + user["username"]) if user.get("username") else user.get("first_name", "Жнец")
    return int(user["id"]), name


def rpc(name, params):
    try:
        return sb.rpc(name, params).execute().data
    except Exception as e:  # noqa: BLE001
        print(f"[event] rpc {name} failed: {e}")
        raise ApiError(500, "rpc_failed")


def secs_until(ts, plus=0):
    if not ts:
        return 0
    t = datetime.fromisoformat(ts.replace("Z", "+00:00")) + timedelta(seconds=plus)
    return max(0, int((t - datetime.now(timezone.utc)).total_seconds()))


# ---------- эндпоинты ----------
@bp.route("/profile", methods=["POST"])
def profile():
    uid, name = auth(body())
    p = rpc("event_ensure_profile", {"p_user": uid, "p_username": name})

    stars_balance, converted_today = 0.0, 0.0
    try:
        # user_id в users может быть int8 или text — пробуем оба варианта
        row = sb.table("users").select("stars").eq("user_id", uid).execute().data
        if not row:
            row = sb.table("users").select("stars").eq("user_id", str(uid)).execute().data
        if row:
            stars_balance = float(row[0].get("stars") or 0)
        since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        conv = (
            sb.table("event_conversions").select("stars")
            .eq("user_id", uid).gte("created_at", since).execute().data
        )
        converted_today = float(sum(float(c["stars"]) for c in conv))
    except Exception as e:  # noqa: BLE001
        print(f"[event] profile extras failed: {e}")

    return jsonify({
        "souls": p["souls_balance"],
        "collected": p["souls_collected_total"],
        "stolen": p["souls_stolen_total"],
        "lost": p["souls_lost_total"],
        "wins": p["wins"],
        "losses": p["losses"],
        "draws": p["draws"],
        "shield_left": secs_until(p.get("shield_until")),
        "harvest_wait": secs_until(p.get("last_harvest_at"), CFG["harvest_cooldown"]),
        "stars_balance": stars_balance,
        "converted_today": converted_today,
        "cfg": CFG,
    })


@bp.route("/harvest", methods=["POST"])
def harvest():
    uid, _ = auth(body())
    return jsonify(rpc("event_harvest", {"p_user": uid}))


@bp.route("/shield", methods=["POST"])
def shield():
    uid, _ = auth(body())
    return jsonify(rpc("event_buy_shield", {"p_user": uid}))


@bp.route("/battle/search", methods=["POST"])
def battle_search():
    uid, name = auth(body())
    return jsonify(rpc("event_find_match", {"p_user": uid, "p_username": name}))


@bp.route("/battle/cancel", methods=["POST"])
def battle_cancel():
    uid, _ = auth(body())
    rpc("event_cancel_search", {"p_user": uid})
    return jsonify({"ok": True})


@bp.route("/battle/move", methods=["POST"])
def battle_move():
    data = body()
    uid, _ = auth(data)
    battle_id = data.get("battle_id")
    spell = data.get("spell")
    if not battle_id or not spell:
        raise ApiError(400, "battle_id and spell required")
    return jsonify(rpc("event_submit_move", {"p_user": uid, "p_battle": battle_id, "p_spell": spell}))


@bp.route("/battle/state", methods=["POST"])
def battle_state():
    data = body()
    uid, _ = auth(data)
    battle_id = data.get("battle_id")
    if not battle_id:
        raise ApiError(400, "battle_id required")
    return jsonify(rpc("event_battle_state", {"p_user": uid, "p_battle": battle_id}))


@bp.route("/convert", methods=["POST"])
def convert():
    data = body()
    uid, _ = auth(data)
    try:
        stars = int(data.get("stars", 0))
    except (TypeError, ValueError):
        raise ApiError(400, "bad stars")
    return jsonify(rpc("event_convert", {"p_user": uid, "p_stars": stars}))


@bp.route("/rating", methods=["POST"])
def rating():
    data = body()
    uid, _ = auth(data)
    col = "souls_balance" if data.get("kind") == "souls" else "souls_stolen_total"
    try:
        rows = (
            sb.table("event_profiles")
            .select("user_id,username,souls_balance,souls_stolen_total,wins")
            .order(col, desc=True)
            .limit(50)
            .execute()
            .data
        )
    except Exception as e:  # noqa: BLE001
        print(f"[event] rating failed: {e}")
        raise ApiError(500, "rating_failed")

    return jsonify({
        "items": [
            {
                "rank": i + 1,
                "name": r.get("username") or "Жнец",
                "souls": r["souls_balance"],
                "stolen": r["souls_stolen_total"],
                "wins": r["wins"],
                "is_me": r["user_id"] == uid,
            }
            for i, r in enumerate(rows)
        ]
    })
