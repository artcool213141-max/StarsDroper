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

GIFT_DATABASE = {
    "1may.jpg": {"name": "1 May Exclusive", "price": 100, "img": "1may.jpg"},
    "1may.png": {"name": "1 May Classic", "price": 100, "img": "1may.png"},
    "chassiki.png": {"name": "Golden Watches", "price": 4700, "img": "chassiki.png"},
    "sliva.png": {"name": "Juicy Plum Jackpot", "price": 33500, "img": "sliva.png"},
    "soska.png": {"name": "Super Pacifier", "price": 2500, "img": "soska.png"},
    "zirka.png": {"name": "Shiny Starlet", "price": 850, "img": "zirka.png"},
    "2025.jpg": {"name": "Happy 2025", "price": 500, "img": "2025.jpg"},
    "bear.png": {"name": "Honey Bear", "price": 3500, "img": "bear.png"},
    "book.jpg": {"name": "Ancient Book", "price": 1000, "img": "book.jpg"},
    "booox.png": {"name": "Berry Box", "price": 700, "img": "booox.png"},
    "botinok.png": {"name": "Old Boot", "price": 400, "img": "botinok.png"},
    "box.png": {"name": "Jack in Box", "price": 600, "img": "box.png"},
    "car.png": {"name": "Sports Car", "price": 5000, "img": "car.png"},
    "raketa.png": {"name": "Space Rocket", "price": 50, "img": "raketa.png"},
    "ccolso2.png": {"name": "Star Ring", "price": 3000, "img": "ccolso2.png"},
    "cerrrdce.jpg": {"name": "Gingerbread", "price": 500, "img": "cerrrdce.jpg"},
    "chemodan.jpg": {"name": "Traveler Case", "price": 5000, "img": "chemodan.jpg"},
    "ciga.png": {"name": "Luxury Cigar", "price": 3000, "img": "ciga.png"},
    "colso.png": {"name": "Blue Diamond", "price": 2500, "img": "colso.png"},
    "costum.jpg": {"name": "Royal Costume", "price": 10000, "img": "costum.jpg"},
    "cvetok.png": {"name": "Wild Flower", "price": 1000, "img": "cvetok.png"},
    "dog.png": {"name": "Rich Dog", "price": 500, "img": "dog.png"},
    "dyxi.png": {"name": "Gold Perfume", "price": 10000, "img": "dyxi.png"},
    "fonarik.jpg": {"name": "Night Lantern", "price": 100, "img": "fonarik.jpg"},
    "grob.jpg": {"name": "Ancient Coffin", "price": 5000, "img": "grob.jpg"},
    "gyba.png": {"name": "Lava Lips", "price": 5000, "img": "gyba.png"},
    "happybirthday.jpg": {"name": "Birthday Cake", "price": 200, "img": "happybirthday.jpg"},
    "heart.png": {"name": "Heart Lock", "price": 2000, "img": "heart.png"},
    "helmet.png": {"name": "Spartan Helmet", "price": 25000, "img": "helmet.png"},
    "kalendar.png": {"name": "Event Calendar", "price": 400, "img": "kalendar.png"},
    "kepka.png": {"name": "Legendary Cap", "price": 100000, "img": "kepka.png"},
    "kirpitch.jpg": {"name": "Golden Brick", "price": 10000, "img": "kirpitch.jpg"},
    "koks.jpg": {"name": "Party Cocktail", "price": 150, "img": "koks.jpg"},
    "koktel.png": {"name": "Toxic Mix", "price": 500, "img": "koktel.png"},
    "kot.png": {"name": "Atomic Cat", "price": 10000, "img": "kot.png"},
    "kotel.png": {"name": "Witch Cauldron", "price": 500, "img": "kotel.png"},
    "krovatka.jpg": {"name": "Baby Bow", "price": 600, "img": "krovatka.jpg"},
    "lolipop.png": {"name": "Sweet Lollipop", "price": 500, "img": "lolipop.png"},
    "lucky.jpg": {"name": "Clover Lucky", "price": 500, "img": "lucky.jpg"},
    "mafin.jpg": {"name": "Sugar Muffin", "price": 700, "img": "mafin.jpg"},
    "metch.png": {"name": "Star Saber", "price": 700, "img": "metch.png"},
    "narkotiki.png": {"name": "Star Token", "price": 700, "img": "narkotiki.png"},
    "obyv.jpg": {"name": "Sneakers Pro", "price": 10000, "img": "obyv.jpg"},
    "orel.jpg": {"name": "Golden Eagle", "price": 5000, "img": "orel.jpg"},
    "otkritka.jpg": {"name": "Peace Dove", "price": 150, "img": "otkritka.jpg"},
    "paska.jpg": {"name": "Easter Cake", "price": 75, "img": "paska.jpg"},
    "rozza.png": {"name": "Velvet Rose", "price": 2000, "img": "rozza.png"},
    "rykzak.jpg": {"name": "Adventurer Bag", "price": 500, "img": "rykzak.jpg"},
    "shapka.png": {"name": "Santa Hat", "price": 500, "img": "shapka.png"},
    "shar.jpg": {"name": "Magic Ball", "price": 1000, "img": "shar.jpg"},
    "shlem.png": {"name": "Biker Helmet", "price": 3500, "img": "shlem.png"},
    "soska.jpg": {"name": "Diamond Pacifier", "price": 3000, "img": "soska.jpg"},
    "star.png": {"name": "Pure Star", "price": 5, "img": "star.png"},
    "statyya.jpg": {"name": "Hero Statue", "price": 41000, "img": "statyya.jpg"},
    "venok.png": {"name": "Wreath Flower", "price": 500, "img": "venok.png"},
    "yayko.png": {"name": "Dragon Egg", "price": 600, "img": "yayko.png"},
    "zhele.png": {"name": "Slime Jelly", "price": 700, "img": "zhele.png"},
    "zmei.png": {"name": "Snake Friend", "price": 500, "img": "zmei.png"},
    "meczcc.png": {"name": "Faith Amulet", "price": 600, "img": "meczcc.png"},
    "kryg.png": {"name": "Snow Globe", "price": 600, "img": "kryg.png"},
    "gribb.png": {"name": "Spy Agaric", "price": 600, "img": "gribb.png"},
    "zirka.png": {"name": "Hanging Star", "price": 800, "img": "zirka.png"},
    "cvetk.png": {"name": "Sakura Flower", "price": 900, "img": "cvetk.png"},
    "sshapka.png": {"name": "Khabib's Papakha", "price": 2300, "img": "sshapka.png"},
    "tyfli.png": {"name": "Sky Stilettos", "price": 1800, "img": "tyfli.png"}
}
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
