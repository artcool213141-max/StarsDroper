import { createClient } from '@supabase/supabase-js';

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

export default async function handler(req, res) {
    // 1. СРАЗУ отвечаем Telegram, что всё получили
    res.status(200).send('OK');

    const update = req.body;
    
    // 2. Обрабатываем логику дальше
    if (update.message?.successful_payment) {
        const payment = update.message.successful_payment;
        const userId = payment.invoice_payload; 
        const starsReceived = payment.total_amount;

        console.log(`Обработка платежа: ${starsReceived} звезд для ${userId}`);

        try {
            // Получаем текущий баланс
            const { data: user } = await supabase
                .from('users')
                .select('stars')
                .eq('user_id', userId)
                .single();

            const currentStars = user?.stars || 0;
            const newStars = currentStars + starsReceived;

            // Обновляем базу
            await supabase
                .from('users')
                .update({ stars: newStars })
                .eq('user_id', userId);

            console.log(`УСПЕХ: Баланс ${userId} обновлен до ${newStars}`);
        } catch (err) {
            console.error("Критическая ошибка при обновлении БД:", err);
        }
    }
}
