import { createClient } from '@supabase/supabase-js';

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    // Пробуем взять user_id из query. Если фронтенд шлет /api/get_balance/12345, 
    // Vercel может записать остаток пути в req.url. Сделаем универсальный поиск ID:
    let user_id = req.query.user_id;
    
    if (!user_id) {
        // Извлекаем любые цифры из конца строки URL (на случай путей типа /get_balance/12345)
        const match = req.url.match(/\/(\d+)/);
        if (match) user_id = match[1];
    }

    if (!user_id) {
        return res.status(400).json({ error: 'Missing user_id' });
    }

    try {
        const { data, error } = await supabase
            .from('users_state')
            .select('*')
            .eq('user_id', user_id)
            .maybeSingle(); // maybeSingle безопаснее, он не спамит ошибками если юзера нет

        if (error) throw error;

        if (!data) {
            return res.status(200).json({
                points: 0,
                energy: 1000,
                max_energy: 1000,
                click_power: 1,
                active_hero_id: 0,
                owned_heroes: [0],
                market_levels: {}
            });
        }

        // Преобразуем bigint id в строку БЕЗОПАСНО для JSON
        if (data.user_id) {
            data.user_id = data.user_id.toString();
        }

        return res.status(200).json(data);
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
}
