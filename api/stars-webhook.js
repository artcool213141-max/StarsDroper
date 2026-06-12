import { createClient } from '@supabase/supabase-js';
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

export default async function handler(req, res) {
    const update = req.body;
    
    // Телеграм присылает событие успешной оплаты
    if (update.message?.successful_payment) {
        const payment = update.message.successful_payment;
        const userId = payment.invoice_payload; 
        const starsReceived = payment.total_amount; // Это количество ЗВЁЗД

        console.log(`Зачисление ${starsReceived} звезд пользователю ${userId}`);

        // 1. Сначала получаем текущий баланс
        const { data: user, error: fetchError } = await supabase
            .from('users')
            .select('stars')
            .eq('user_id', userId)
            .single();

        if (fetchError) {
            console.error("Ошибка при получении юзера:", fetchError);
            return res.status(200).send('OK');
        }

        // 2. Считаем новый баланс (если stars null, берем 0)
        const currentStars = user?.stars || 0;
        const newStars = currentStars + starsReceived;

        // 3. Обновляем базу
        const { error: updateError } = await supabase
            .from('users')
            .update({ stars: newStars })
            .eq('user_id', userId);

        if (updateError) {
            console.error("Ошибка при обновлении баланса:", updateError);
        } else {
            console.log(`УСПЕХ: Баланс звезд ${userId} теперь ${newStars}`);
        }
    }
    
    return res.status(200).send('OK'); 
}
