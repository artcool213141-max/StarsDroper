import { createClient } from '@supabase/supabase-js';

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        // Берем топ-20 игроков по количеству поинтов из таблицы users_state
        const { data, error } = await supabase
            .from('users_state')
            .select('user_id, username, points')
            .order('points', { ascending: false })
            .limit(20);

        if (error) throw error;

        // Если данных вообще нет в базе
        if (!data) {
            return res.status(200).json([]);
        }

        // Безопасно превращаем BigInt/числа в строку для корректной передачи в JSON
        const formattedData = data.map(user => ({
            ...user,
            user_id: user.user_id ? user.user_id.toString() : '0',
            points: Number(user.points) || 0
        }));

        return res.status(200).json(formattedData);
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
}
