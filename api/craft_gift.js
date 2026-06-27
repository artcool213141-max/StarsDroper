import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

const giftDatabase = {
        "1may.jpg": { name: "1 May Exclusive", price: 100, img: "1may.jpg" },
        "1may.png": { name: "1 May Classic", price: 100, img: "1may.png" }, 
        "chassiki.png": { name: "Golden Watches", price: 4700, img: "chassiki.png" }, 
        "sliva.png": { name: "Juicy Plum Jackpot", price: 33500, img: "sliva.png" }, 
        "soska.png": { name: "Super Pacifier", price: 2500, img: "soska.png" }, 
        "zirka.png": { name: "Shiny Starlet", price: 850, img: "zirka.png" }, 
        "2025.jpg": { name: "Happy 2025", price: 500, img: "2025.jpg" },
        "bear.png": { name: "Honey Bear", price: 3500, img: "bear.png" },
        "book.jpg": { name: "Ancient Book", price: 1000, img: "book.jpg" },
        "booox.png": { name: "Berry Box", price: 700, img: "booox.png" },
        "botinok.png": { name: "Old Boot", price: 400, img: "botinok.png" },
        "box.png": { name: "Jack in Box", price: 600, img: "box.png" },
        "car.png": { name: "Sports Car", price: 5000, img: "car.png" },
        "raketa.png": { name: "Space Rocket", price: 50, img: "raketa.png" },
        "ccolso2.png": { name: "Star Ring", price: 3000, img: "ccolso2.png" },
        "cerrrdce.jpg": { name: "Gingerbread", price: 500, img: "cerrrdce.jpg" },
        "chemodan.jpg": { name: "Traveler Case", price: 5000, img: "chemodan.jpg" },
        "ciga.png": { name: "Luxury Cigar", price: 3000, img: "ciga.png" },
        "colso.png": { name: "Blue Diamond", price: 2500, img: "colso.png" },
        "costum.jpg": { name: "Royal Costume", price: 10000, img: "costum.jpg" },
        "cvetok.png": { name: "Wild Flower", price: 1000, img: "cvetok.png" },
        "dog.png": { name: "Rich Dog", price: 500, img: "dog.png" },
        "dyxi.png": { name: "Gold Perfume", price: 10000, img: "dyxi.png" },
        "fonarik.jpg": { name: "Night Lantern", price: 100, img: "fonarik.jpg" },
        "grob.jpg": { name: "Ancient Coffin", price: 5000, img: "grob.jpg" },
        "gyba.png": { name: "Lava Lips", price: 5000, img: "gyba.png" },
        "happybirthday.jpg": { name: "Birthday Cake", price: 200, img: "happybirthday.jpg" },
        "heart.png": { name: "Heart Lock", price: 2000, img: "heart.png" },
        "helmet.png": { name: "Spartan Helmet", price: 25000, img: "helmet.png" },
        "kalendar.png": { name: "Event Calendar", price: 400, img: "kalendar.png" },
        "kepka.png": { name: "Legendary Cap", price: 100000, img: "kepka.png" },
        "kirpitch.jpg": { name: "Golden Brick", price: 10000, img: "kirpitch.jpg" },
        "koks.jpg": { name: "Party Cocktail", price: 150, img: "koks.jpg" },
        "koktel.png": { name: "Toxic Mix", price: 500, img: "koktel.png" },
        "kot.png": { name: "Atomic Cat", price: 10000, img: "kot.png" },
        "kotel.png": { name: "Witch Cauldron", price: 500, img: "kotel.png" },
        "krovatka.jpg": { name: "Baby Bow", price: 600, img: "krovatka.jpg" },
        "lolipop.png": { name: "Sweet Lollipop", price: 500, img: "lolipop.png" },
        "lucky.jpg": { name: "Clover Lucky", price: 500, img: "lucky.jpg" },
        "mafin.jpg": { name: "Sugar Muffin", price: 700, img: "mafin.jpg" },
        "metch.png": { name: "Star Saber", price: 700, img: "metch.png" },
        "narkotiki.png": { name: "Star Token", price: 700, img: "narkotiki.png" },
        "obyv.jpg": { name: "Sneakers Pro", price: 10000, img: "obyv.jpg" },
        "orel.jpg": { name: "Golden Eagle", price: 5000, img: "orel.jpg" },
        "otkritka.jpg": { name: "Peace Dove", price: 150, img: "otkritka.jpg" },
        "paska.jpg": { name: "Easter Cake", price: 75, img: "paska.jpg" },
        "rozza.png": { name: "Velvet Rose", price: 2000, img: "rozza.png" },
        "rykzak.jpg": { name: "Adventurer Bag", price: 500, img: "rykzak.jpg" },
        "shapka.png": { name: "Santa Hat", price: 500, img: "shapka.png" },
        "shar.jpg": { name: "Magic Ball", price: 1000, img: "shar.jpg" },
        "shlem.png": { name: "Biker Helmet", price: 3500, img: "shlem.png" },
        "soska.jpg": { name: "Diamond Pacifier", price: 3000, img: "soska.jpg" },
        "star.png": { name: "Pure Star", price: 5, img: "star.png" },
        "statyya.jpg": { name: "Hero Statue", price: 41000, img: "statyya.jpg" },
        "venok.png": { name: "Wreath Flower", price: 500, img: "venok.png" },
        "yayko.png": { name: "Dragon Egg", price: 600, img: "yayko.png" },
        "zhele.png": { name: "Slime Jelly", price: 700, img: "zhele.png" },
        "zmei.png": { name: "Snake Friend", price: 500, img: "zmei.png" },
        "meczcc.png": { name: "Faith Amulet", price: 600, img: "meczcc.png" },
        "kryg.PNG": { name: "Snow Globe", price: 600, img: "kryg.PNG" },
        "gribb.PNG": { name: "Spy Agaric", price: 600, img: "gribb.PNG" },
        "zirka.PNG": { name: "Hanging Star", price: 800, img: "zirka.PNG" },
        "cvetk.PNG": { name: "Sakura Flower", price: 900, img: "cvetk.PNG" },
        "sshapka.PNG": { name: "Khabib's Papakha", price: 2300, img: "sshapka.PNG" },
        "tyfli.PNG": { name: "Sky Stilettos", price: 1800, img: "tyfli.PNG" }
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
