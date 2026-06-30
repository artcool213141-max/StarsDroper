import { createClient } from '@supabase/supabase-js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
 
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);
 
// Вспомогательная функция для получения чистого ключа
const getGiftKey = (item) => {
    if (typeof item === 'string') return item.replace('img/', '');
    if (typeof item === 'object' && item !== null && item.img) return item.img.replace('img/', '');
    return null;
};
 
// ====== Загрузка базы подарков из внешнего items.js ======
// Структура проекта (пример):
//   /index.html
//   /craft.html
//   /items.js            <-- файл с подарками лежит здесь, в корне
//   /img/...
//   /api/craft_gift.js   <-- этот файл, лежит в папке api
//
// items.js остаётся обычным браузерным файлом вида:
//   const giftDatabase = { ... };
// Поэтому мы не делаем import, а читаем файл как текст,
// вырезаем JSON-часть между первой "{" и последней "}" и парсим её.
 
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ITEMS_PATH = path.join(__dirname, '..', 'items.js');
 
function loadGiftDatabase() {
    try {
        const raw = fs.readFileSync(ITEMS_PATH, 'utf-8');
        const start = raw.indexOf('{');
        const end = raw.lastIndexOf('}');
        if (start === -1 || end === -1) {
            throw new Error('Не удалось найти JSON-объект внутри items.js');
        }
        const jsonPart = raw.slice(start, end + 1);
        return JSON.parse(jsonPart);
    } catch (e) {
        console.error('Ошибка загрузки items.js:', e);
        return {};
    }
}
 
const giftDatabase = loadGiftDatabase();
// ============================================================
 
export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
 
    if (req.method === 'OPTIONS') return res.status(200).end();
 
    if (Object.keys(giftDatabase).length === 0) {
        return res.status(500).json({ error: 'База подарков не загружена (items.js)' });
    }
 
    if (req.method === 'GET') {
        const { user_id } = req.query;
        if (!user_id) return res.status(400).json({ error: 'Не указан user_id' });
 
        const { data: user } = await supabase.from('users').select('inventory').eq('user_id', String(user_id)).single();
        const inv = Array.isArray(user?.inventory) ? user.inventory : [];
        return res.status(200).json({ success: true, inventory: inv });
    }
 
    if (req.method === 'POST') {
        const { user_id, gift_keys } = req.body;
        
        if (!user_id || !gift_keys || !Array.isArray(gift_keys) || gift_keys.length !== 5) {
            return res.status(400).json({ error: 'Передайте ровно 5 предметов.' });
        }
 
        let totalPrice = 0;
        for (const key of gift_keys) {
            const cleanKey = getGiftKey(key);
            if (!giftDatabase[cleanKey]) {
                return res.status(400).json({ error: `Предмет ${cleanKey} не найден в базе.` });
            }
            totalPrice += giftDatabase[cleanKey].price;
        }
 
        const { data: user, error: userError } = await supabase
            .from('users')
            .select('inventory')
            .eq('user_id', String(user_id))
            .single();
 
        if (userError || !user) return res.status(400).json({ error: 'Пользователь не найден.' });
 
        let tempInventory = [...(Array.isArray(user.inventory) ? user.inventory : [])];
 
        for (const key of gift_keys) {
            const cleanKey = getGiftKey(key);
            const index = tempInventory.findIndex(item => getGiftKey(item) === cleanKey);
            
            if (index === -1) {
                return res.status(400).json({ error: `Предмет ${cleanKey} отсутствует в инвентаре.` });
            }
            tempInventory.splice(index, 1);
        }
 
        const rand = Math.random() * 100;
        let pool = Object.keys(giftDatabase).filter(k => {
            const p = giftDatabase[k].price;
            if (rand <= 30) return p >= totalPrice * 0.1 && p <= totalPrice * 0.6;
            if (rand <= 70) return p >= totalPrice * 0.8 && p <= totalPrice * 1.2;
            return p >= totalPrice * 1.3 && p <= totalPrice * 2.5;
        });
 
        if (pool.length === 0) pool = Object.keys(giftDatabase);
        const winKey = pool[Math.floor(Math.random() * pool.length)];
        const winData = giftDatabase[winKey];
 
        const newItem = {
            id: Date.now() + Math.random(),
            img: "img/" + winData.img,
            name: winData.name,
            price: winData.price
        };
 
        const updatedInventory = [...tempInventory, newItem];
        
        await supabase
            .from('users')
            .update({ inventory: updatedInventory })
            .eq('user_id', String(user_id));
 
        return res.status(200).json({ success: true, new_gift_key: winKey });
    }
}
