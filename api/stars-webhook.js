import { createClient } from '@supabase/supabase-js';
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

export default async function handler(req, res) {
    const update = req.body;
    
    // Ловим событие успешного платежа
    if (update.message?.successful_payment) {
        const payment = update.message.successful_payment;
        const userId = payment.invoice_payload; // Тот самый ID, который ты передал выше
        const starsReceived = payment.total_amount;

        // Зачисляем в БД
        await supabase
            .from('users')
            .update({ stars: currentStars + starsReceived }) // Убедись, что колонка называется stars
            .eq('user_id', userId);
    }
    
    return res.status(200).send('OK');
}
