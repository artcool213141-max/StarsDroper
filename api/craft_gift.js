import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

const giftDatabase = {
    "1may.jpg": { price: 100 }, "1may.png": { price: 100 }, "chassiki.png": { price: 4700 }, 
    "sliva.png": { price: 33500 }, "soska.png": { price: 2500 }, "zirka.png": { price: 850 }, 
    "2025.jpg": { price: 500 }, "bear.png": { price: 3500 }, "book.jpg": { price: 1000 }, 
    "booox.png": { price: 700 }, "botinok.png": { price: 400 }, "box.png": { price: 600 }, 
    "car.png": { price: 5000 }, "raketa.png": { price: 50 }, "ccolso2.png": { price: 3000 }, 
    "cerrrdce.jpg": { price: 500 }, "chemodan.jpg": { price: 5000 }, "ciga.png": { price: 3000 }, 
    "colso.png": { price: 2500 }, "costum.jpg": { price: 10000 }, "cvetok.png": { price: 1000 }, 
    "dog.png": { price: 500 }, "dyxi.png": { price: 10000 }, "fonarik.jpg": { price: 100 }, 
    "grob.jpg": { price: 5000 }, "gyba.png": { price: 5000 }, "happybirthday.jpg": { price: 200 }, 
    "heart.png": { price: 2000 }, "helmet.png": { price: 25000 }, "kalendar.png": { price: 400 }, 
    "kepka.png": { price: 100000 }, "kirpitch.jpg": { price: 10000 }, "koks.jpg": { price: 150 }, 
    "koktel.png": { price: 500 }, "kot.png": { price: 10000 }, "kotel.png": { price: 500 }, 
    "krovatka.jpg": { price: 600 }, "lolipop.png": { price: 500 }, "lucky.jpg": { price: 500 }, 
    "mafin.jpg": { price: 700 }, "metch.png": { price: 700 }, "narkotiki.png": { price: 700 }, 
    "obyv.jpg": { price: 10000 }, "orel.jpg": { price: 5000 }, "otkritka.jpg": { price: 150 }, 
    "paska.jpg": { price: 75 }, "rozza.png": { price: 2000 }, "rykzak.jpg": { price: 500 }, 
    "shapka.png": { price: 500 }, "shar.jpg": { price: 1000 }, "shlem.png": { price: 3500 }, 
    "soska.jpg": { price: 3000 }, "star.png": { price: 5 }, "statyya.jpg": { price: 41000 }, 
    "venok.png": { price: 500 }, "yayko.png": { price: 600 }, "zhele.png": { price: 700 }, 
    "zmei.png": { price: 500 }, "meczcc.png": { price: 600 }, "kryg.PNG": { price: 600 }, 
    "gribb.PNG": { price: 600 }, "zirka.PNG": { price: 800 }, "cvetk.PNG": { price: 900 }, 
    "sshapka.PNG": { price: 2300 }, "tyfli.PNG": { price: 1800 }
};

export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');

    if (req.method === 'OPTIONS') return res.status(200).end();

    // ==========================================
    // ЛОГИКА ПОЛУЧЕНИЯ ИНВЕНТАРЯ (GET)
    // ==========================================
    if (req.method === 'GET') {
        try {
            const { user_id } = req.query;
            if (!user_id) return res.status(400).json({ error: 'Не указан user_id' });

            const { data: user, error: userError } = await supabase
                .from('users')
                .select('inventory')
                .eq('user_id', String(user_id))
                .single();

            if (userError || !user) {
                // Если юзера нет в базе, можно вернуть пустой массив, чтобы не крашить фронт
                return res.status(200).json({ success: true, inventory: [] });
            }

            const inv = Array.isArray(user.inventory) ? user.inventory : [];
            return res.status(200).json({ success: true, inventory: inv });
        } catch (err) {
            return res.status(500).json({ error: 'Ошибка сервера при получении инвентаря' });
        }
    }

    // ==========================================
    // ЛОГИКА КРАФТА (POST)
    // ==========================================
    if (req.method === 'POST') {
        try {
            const { user_id, gift_keys } = req.body;
            if (!user_id || !gift_keys || gift_keys.length !== 5) {
                return res.status(400).json({ error: 'Передайте ровно 5 предметов.' });
            }

            let totalPrice = 0;
            for (const key of gift_keys) {
                if (!giftDatabase[key]) return res.status(400).json({ error: `Предмет ${key} не найден.` });
                totalPrice += giftDatabase[key].price;
            }

            const { data: user, error: userError } = await supabase
                .from('users')
                .select('inventory')
                .eq('user_id', String(user_id))
                .single();
                
            if (userError || !user) return res.status(404).json({ error: 'Пользователь не найден.' });

            let currentInventory = Array.isArray(user.inventory) ? user.inventory : [];

            let tempInventory = [...currentInventory];
            for (const key of gift_keys) {
                const index = tempInventory.indexOf(key);
                if (index === -1) return res.status(400).json({ error: 'Не хватает предметов в инвентаре!' });
                tempInventory.splice(index, 1);
            }
            currentInventory = tempInventory;

            const rand = Math.random() * 100;
            let pool = [];

            if (rand <= 30) {
                pool = Object.keys(giftDatabase).filter(k => giftDatabase[k].price >= totalPrice * 0.1 && giftDatabase[k].price <= totalPrice * 0.6);
            } else if (rand <= 70) {
                pool = Object.keys(giftDatabase).filter(k => giftDatabase[k].price >= totalPrice * 0.8 && giftDatabase[k].price <= totalPrice * 1.2);
            } else {
                pool = Object.keys(giftDatabase).filter(k => giftDatabase[k].price >= totalPrice * 1.3 && giftDatabase[k].price <= totalPrice * 2.5);
            }

            if (pool.length === 0) {
                pool = Object.keys(giftDatabase);
            }

            const winKey = pool[Math.floor(Math.random() * pool.length)];

            currentInventory.push(winKey);
            await supabase.from('users').update({ inventory: currentInventory }).eq('user_id', String(user_id));

            return res.status(200).json({ success: true, new_gift_key: winKey });

        } catch (err) {
            return res.status(500).json({ error: 'Ошибка сервера при крафте' });
        }
    }

    return res.status(405).json({ error: 'Method not allowed' });
}
