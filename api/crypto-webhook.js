import { createClient } from '@supabase/supabase-js';
import crypto from 'crypto';

const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

export default async function handler(req, res) {
    if (req.method !== 'POST') return res.status(200).send('OK');

    try {
        // Проверка подписи (если она включена в настройках CryptoBot)
        const signature = req.headers['crypto-pay-api-signature'];
        if (signature) {
            const apiSecret = crypto.createHash('sha256').update(process.env.CRYPTO_BOT_TOKEN).digest();
            const check = crypto.createHmac('sha256', apiSecret).update(JSON.stringify(req.body)).digest('hex');
            if (signature !== check) return res.status(401).send('Unauthorized');
        }

        // РАЗБОР ДАННЫХ (Адаптировано под твой текущий формат логов)
        const { update_type, payload } = req.body;

        if (update_type === 'invoice_paid') {
            // ВАЖНО: берем данные из объекта payload, который прислал бот
            const userId = String(payload.invoice_payload); 
            const sum = parseFloat(payload.amount);
            
            console.log(`Зачисление: ${sum} для юзера ${userId}`);

            // 1. Получаем текущий баланс (используем имя колонки из РАБОЧЕГО файла!)
            const { data: user } = await supabase
                .from('users')
                .select('ton_balance') 
                .eq('user_id', userId)
                .single();

            const currentBalance = user?.ton_balance || 0;
            const newBalance = currentBalance + sum;

            // 2. Обновляем (используем UPSERT, как в рабочем коде)
            const { error: updateError } = await supabase
                .from('users')
                .upsert({ 
                    user_id: userId, 
                    ton_balance: newBalance 
                }, { onConflict: 'user_id' });

            if (updateError) throw updateError;
            console.log(`УСПЕХ! Баланс ${userId} теперь: ${newBalance}`);
        }

        return res.status(200).send('OK');
    } catch (err) {
        console.error("Ошибка:", err.message);
        return res.status(200).send('OK'); // Всегда 200, чтобы не спамил
    }
}
