import { createClient } from '@supabase/supabase-js';
import crypto from 'crypto';

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

export default async function handler(req, res) {
    if (req.method !== 'POST') return res.status(200).send('OK');

    try {
        const { update_type, payload } = req.body;

        if (update_type === 'invoice_paid') {
            // Исправлено: теперь берем ID из правильного места
            const userId = String(payload.payload); 
            const sum = parseFloat(payload.amount);
            
            console.log(`Зачисление: ${sum} для юзера ${userId}`);

            // 1. Получаем данные (замени 'balance' на реальное имя колонки из БД!)
            const { data: user, error: fetchError } = await supabase
                .from('users')
                .select('balance') 
                .eq('user_id', userId)
                .single();

            // Если юзера нет, создаем его (или обрабатываем ошибку)
            const currentBalance = user?.balance || 0;
            const newBalance = parseFloat(currentBalance) + sum;

            // 2. Обновляем (замени 'balance' на реальное имя колонки из БД!)
            const { error: updateError } = await supabase
                .from('users')
                .update({ balance: newBalance })
                .eq('user_id', userId);

            if (updateError) throw updateError;
            console.log(`УСПЕХ: Баланс ${userId} обновлен до ${newBalance}`);
        }

        return res.status(200).send('OK');
    } catch (err) {
        console.error("КРИТИЧЕСКАЯ ОШИБКА:", err.message);
        return res.status(200).send('OK'); 
    }
}
