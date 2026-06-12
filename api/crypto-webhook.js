import { createClient } from '@supabase/supabase-js';
import crypto from 'crypto';

const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ message: "Только POST запросы" });
    }

    try {
        // 1. ПРОВЕРКА ПОДПИСИ (Безопасность)
        // Чтобы никто кроме CryptoBot не мог начислять баланс
        const signature = req.headers['crypto-pay-api-signature'];
        const apiSecret = crypto.createHash('sha256').update(process.env.CRYPTO_BOT_TOKEN).digest();
        const check = crypto.createHmac('sha256', apiSecret).update(JSON.stringify(req.body)).digest('hex');

        if (signature !== check) {
            console.error("ВНИМАНИЕ: Попытка неавторизованного доступа!");
            return res.status(401).send('Unauthorized');
        }

        const { status, payload, amount, asset } = req.body;

        // 2. Обработка успешного платежа
        if (status === 'paid' && asset === 'TON') {
            const userId = String(payload); 
            const sum = parseFloat(amount);

            console.log(`Начисление ${sum} TON юзеру ${userId}`);

            // 3. Вызов SQL функции для безопасного обновления баланса
            const { error } = await supabase.rpc('increment_ton_balance', { 
                user_id_val: userId, 
                amount_val: sum 
            });

            if (error) throw error;
            console.log("Баланс успешно обновлен в Supabase");
        }

        return res.status(200).send('OK');

    } catch (err) {
        console.error("Ошибка вебхука:", err.message);
        // Возвращаем 200, чтобы CryptoBot не считал ошибку критической и не спамил
        return res.status(200).send('Processed with error');
    }
}
