import { createClient } from '@supabase/supabase-js';

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

export default async function handler(req, res) {
    if (req.method !== 'POST') return res.status(200).send('OK');

    try {
        const { message, pre_checkout_query } = req.body;
        
        // Автоматическое подтверждение для Telegram Stars
        if (pre_checkout_query) {
            return res.status(200).json({ ok: true });
        }

        const { successful_payment } = req.body.message || {};
        if (successful_payment) {
            const payload = successful_payment.invoice_payload; // "user_12345_amt_50"
            const userId = payload.split('_')[1];
            const amount = parseInt(payload.split('_')[3]);

            console.log(`Зачисление: ${amount} для юзера ${userId}`);

            const { data: user } = await supabase.from('users').select('stars').eq('user_id', userId).single();
            const newStars = (user?.stars || 0) + amount;

            await supabase.from('users').update({ stars: newStars }).eq('user_id', userId);
        }

        return res.status(200).send('OK');
    } catch (err) {
        return res.status(200).send('OK');
    }
}
