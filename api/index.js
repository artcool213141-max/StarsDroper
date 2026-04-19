const express = require('express');
const cors = require('cors');
const axios = require('axios');
const { createClient } = require('@supabase/supabase-js');

const app = express();

// Разрешаем CORS и JSON
app.use(cors());
app.use(express.json());

// Конфигурация из Environment Variables
const supabase = createClient(
    process.env.SUPABASE_URL || '', 
    process.env.SUPABASE_SERVICE_ROLE_KEY || ''
);
const BOT_TOKEN = process.env.BOT_TOKEN;

// --- 1. ПОЛУЧЕНИЕ БАЛАНСА ---
app.get('/api/get_balance/:user_id', async (req, res) => {
    const { user_id } = req.params;
    try {
        const { data, error } = await supabase
            .from('users')
            .select('balance')
            .eq('user_id', String(user_id))
            .single();

        if (error || !data) {
            // Если юзера нет, возвращаем баланс 0
            return res.json({ balance: 0 });
        }
        res.json(data);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// --- 2. СОЗДАНИЕ ОПЛАТЫ ЗВЕЗДАМИ ---
app.post('/api/create_stars_pay', async (req, res) => {
    const { user_id, amount } = req.body;

    if (!BOT_TOKEN) {
        console.error("ОШИБКА: BOT_TOKEN не задан в Vercel!");
        return res.status(500).json({ error: "Server configuration error: No BOT_TOKEN" });
    }

    try {
        const tgUrl = `https://api.telegram.org/bot${BOT_TOKEN}/createInvoiceLink`;
        
        const response = await axios.post(tgUrl, {
            title: "Пополнение баланса",
            description: `Покупка ${amount} звезд`,
            payload: String(user_id),
            provider_token: "", // Для звезд всегда пусто
            currency: "XTR",
            prices: [{ 
                label: "Stars", 
                amount: Math.floor(Number(amount)) // Только целые числа
            }]
        });

        if (response.data.ok) {
            console.log(`Ссылка для ${user_id} создана успешно`);
            res.json({ pay_url: response.data.result });
        } else {
            console.error("TG Error:", response.data);
            res.status(400).json(response.data);
        }
    } catch (e) {
        console.error("Request Error:", e.response?.data || e.message);
        res.status(500).json({ error: "Internal Server Error" });
    }
});

// --- 3. КРИПТО-ВЕБХУК (CryptoBot) ---
app.post('/api/crypto-webhook', async (req, res) => {
    const { status, payload, amount } = req.body;

    if (status === 'paid') {
        const userId = String(payload);
        const paidAmount = parseFloat(amount);

        try {
            // Получаем текущий баланс
            const { data: user } = await supabase
                .from('users')
                .select('balance')
                .eq('user_id', userId)
                .single();

            const currentBalance = user?.balance || 0;
            const newBalance = currentBalance + paidAmount;

            // Обновляем (или создаем) запись
            await supabase
                .from('users')
                .upsert({ user_id: userId, balance: newBalance });

            console.log(`Баланс юзера ${userId} обновлен: +${paidAmount}`);
        } catch (dbError) {
            console.error("DB Error:", dbError.message);
        }
    }
    res.status(200).send('OK');
});

// Роут-заглушка для проверки работоспособности
app.get('/api', (req, res) => {
    res.send('API is running...');
});

// Экспорт для Vercel
module.exports = app;
