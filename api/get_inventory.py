import os
import json
import random
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler
from supabase import create_client, Client
 
# Инициализация Supabase
supabase_url = os.environ.get("SUPABASE_URL", "")
supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
supabase: Client = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None
 
# ====== Загрузка базы подарков из внешнего items.js ======
# Структура проекта (пример):
#   /index.html
#   /craft.html
#   /items.js            <-- файл с подарками лежит здесь, в корне
#   /img/...
#   /api/craft_gift.py   <-- этот файл, лежит в папке api
#
# os.path.dirname(__file__) -> /api
# поднимаемся на 1 уровень вверх ( .. ) -> корень проекта -> ищем items.js
ITEMS_PATH = os.path.join(os.path.dirname(__file__), "..", "items.js")
 
def load_gift_database():
    try:
        with open(ITEMS_PATH, "r", encoding="utf-8") as f:
            raw = f.read()
 
        # items.js выглядит так: const giftDatabase = { ... };
        # Вырезаем всё до первой "{" и всё после последней "}",
        # чтобы получить чистый JSON-объект и распарсить его через json.loads
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Не удалось найти JSON-объект внутри items.js")
 
        json_part = raw[start:end + 1]
        return json.loads(json_part)
    except Exception as e:
        print(f"Ошибка загрузки items.js: {e}")
        return {}
 
GIFT_DATABASE = load_gift_database()
# ============================================================
 
 
class handler(BaseHTTPRequestHandler):
 
    def get_clean_key(self, item):
        if isinstance(item, str):
            return item.lower().replace('img/', '')
        if isinstance(item, dict) and 'img' in item:
            return item['img'].lower().replace('img/', '')
        return str(item).lower()
 
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
 
    def do_GET(self):
        query_components = parse_qs(urlparse(self.path).query)
        user_id = query_components.get("user_id", [None])[0]
 
        inventory = []
        try:
            if user_id:
                response = supabase.table("users").select("inventory").eq("user_id", str(user_id)).execute()
                if response.data and isinstance(response.data, list) and len(response.data) > 0:
                    inventory = response.data[0].get("inventory", [])
        except Exception as e:
            print(f"Ошибка при получении инвентаря: {e}")
 
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"success": True, "inventory": inventory}).encode('utf-8'))
 
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(content_length))
        user_id = body.get("user_id")
        gift_keys = body.get("gift_keys", [])
 
        res = supabase.table("users").select("inventory").eq("user_id", str(user_id)).execute()
        current_inv = res.data[0].get("inventory", []) if res.data else []
        temp_inv = list(current_inv)
 
        # 1. Удаление использованных предметов
        for key in gift_keys:
            clean_request_key = key.lower().replace('img/', '')
            idx = next((i for i, item in enumerate(temp_inv)
                        if self.get_clean_key(item) == clean_request_key), -1)
 
            if idx == -1:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Предмет {key} не найден"}).encode('utf-8'))
                return
            temp_inv.pop(idx)
 
        # 2. Выбор нового подарка
        if not GIFT_DATABASE:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "База подарков не загружена (items.js)"}).encode('utf-8'))
            return
 
        win_key = random.choice(list(GIFT_DATABASE.keys()))
        win_data = GIFT_DATABASE[win_key]
 
        # 3. Добавление объекта в инвентарь
        new_item = {
            "name": win_data["name"],
            "price": win_data["price"],
            "img": "img/" + win_data["img"]
        }
        temp_inv.append(new_item)
 
        # 4. Сохранение
        supabase.table("users").update({"inventory": temp_inv}).eq("user_id", str(user_id)).execute()
 
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"success": True, "new_gift_key": win_key}).encode('utf-8'))
