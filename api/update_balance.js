import { createClient } from '@supabase/supabase-js';

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        const { 
            user_id, username, points, energy, max_energy, 
            click_power, active_hero_id, owned_heroes, market_levels 
        } = req.body;

        if (!user_id) {
            return res.status(400).json({ error: 'Missing user_id' });
        }

        // УБРАЛИ BigInt(user_id) — передаем чистую строку. Supabase поймет её сам.
        const { data, error } = await supabase
            .from('users_state')
            .upsert({
                user_id: user_id.toString(), 
                username: username || 'Anonymous',
                points: Number(points) || 0,
                energy: Number(energy) || 0,
                max_energy: Number(max_energy) || 1000,
                click_power: Number(click_power) || 1,
                active_hero_id: Number(active_hero_id) || 0,
                owned_heroes: owned_heroes || [0],
                market_levels: market_levels || {},
                updated_at: new Date().toISOString()
            }, { onConflict: 'user_id' });

        if (error) throw error;

        return res.status(200).json({ success: true });
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
}
