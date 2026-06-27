import os
import json
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler
from supabase import create_client, Client

# Инициализируем клиент базы данных
supabase_url = os.environ.get("SUPABASE_URL", "")
supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# Если секреты забыли прописать, чтобы код не падал на старте, проверим их наличие
if supabase_url and supabase_key:
    supabase: Client = create_client(supabase_url, supabase_key)
else:
    supabase = None

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if not supabase:
            self.wfile.write(json.dumps({"error": "Supabase credentials are missing on Vercel"}).encode('utf-8'))
            return

        query_components = parse_qs(urlparse(self.path).query)
        user_id_list = query_components.get("user_id")
        
        if not user_id_list:
            self.wfile.write(json.dumps({"error": "No user_id provided"}).encode('utf-8'))
            return

        user_id = user_id_list[0]

        try:
            # Пробуем искать по числовому ID
            query_id = int(user_id) if user_id.isdigit() else user_id
            
            response = supabase.table("users").select("inventory").eq("user_id", query_id).execute()
            
            # Если по числу не вышло, пробуем как строку
            if not response.data:
                response = supabase.table("users").select("inventory").eq("user_id", str(user_id)).execute()

            if response.data:
                inventory = response.data[0].get("inventory", [])
                if not isinstance(inventory, list):
                    inventory = []
                self.wfile.write(json.dumps({"success": True, "inventory": inventory}).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({"success": True, "inventory": []}).encode('utf-8'))

        except Exception as e:
            self.wfile.write(json.dumps({"error": "Server error during DB query", "details": str(e)}).encode('utf-8'))
