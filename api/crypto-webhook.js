import { createClient } from '@supabase/supabase-js';
import crypto from 'crypto';

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

export default async function handler(req, res) {
    if (req.method !== 'POST') return res.status(200).send('OK');

    try {
        // Логируем тело запроса, чтобы видеть структуру
        console.log("ПОЛНЫЙ ЗАПРОС:", JSON.stringify(req.body, null, 2));

        const { update_type, payload } = req.body;

        if (update_type === 'invoice_paid') {
            const userId = String(payload.invoice_payload); 
            const sum = parseFloat(payload.amount);
            
            console.log(`Попытка зачисления: ${sum} для юзера ${userId}`);

            // 1. Получаем данные
            const { data: user, error: fetchError } = await supabase
                .from('users')
                .select('balance') // УБЕДИСЬ: В базе колонка точно ton_balance?
                .eq('user_id', userId)
                .single();

            if (fetchError) {
                console.error("ОШИБКА SELECT:", fetchError);
                // Если юзера нет, возможно, нужно создать?
            }

            const currentBalance = user?.balance || 0;
            const newBalance = parseFloat(currentBalance) + sum;

            // 2. Обновляем
            const { data, error: updateError } = await supabase
                .from('users')
                .update({ balance: newBalance })
                .eq('user_id', userId)
                .select(); // Добавляем select, чтобы увидеть результат

            if (updateError) {
                console.error("ОШИБКА UPDATE:", updateError);
                throw updateError;
            }

            console.log("УСПЕХ. Результат:", data);
        }

        return res.status(200).send('OK');
    } catch (err) {
        console.error("КРИТИЧЕСКАЯ ОШИБКА:", err.message);
        return res.status(200).send('OK'); 
    }
}
