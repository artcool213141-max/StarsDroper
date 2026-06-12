import { createClient } from '@supabase/supabase-js';
import crypto from 'crypto';

const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(200).json({ message: "Webhook active" });
    }

    try {
        const signature = req.headers['crypto-pay-api-signature'];
        const apiSecret = crypto.createHash('sha256').update(process.env.CRYPTO_BOT_TOKEN).digest();
        const check = crypto.createHmac('sha256', apiSecret).update(JSON.stringify(req.body)).digest('hex');
        
        if (signature !== check) return res.status(401).send('Unauthorized');

        // ВАЖНО: Crypto Bot присылает данные в объекте payload
        const { update_type, payload } = req.body;

        if (update_type === 'invoice_paid') {
            const userId = String(payload.invoice_payload); // Твой ID, который ты передавал при создании счета
            const sum = parseFloat(payload.amount);
            const asset = payload.asset;

            if (asset === 'TON') {
                console.log(`Зачисление: ${sum} TON для ${userId}`);

                // 1. Получаем текущий баланс
                const { data: user } = await supabase
                    .from('users')
                    .select('balance') // ПРОВЕРЬ: точно ли колонка называется 'balance'?
                    .eq('user_id', userId)
                    .single();

                const currentBalance = user?.balance || 0;
                const newBalance = parseFloat(currentBalance) + sum;

                // 2. Обновляем баланс
                const { error: updateError } = await supabase
                    .from('users')
                    .update({ balance: newBalance })
                    .eq('user_id', userId);

                if (updateError) throw updateError;
                console.log(`УСПЕХ: Баланс ${userId} = ${newBalance}`);
            }
        }
        return res.status(200).send('OK');
    } catch (err) {
        console.error("Критическая ошибка:", err);
        return res.status(200).send('Error');
    }
}
