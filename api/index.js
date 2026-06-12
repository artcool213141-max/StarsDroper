const express = require('express');
const cors = require('cors');
const axios = require('axios');
const { createClient } = require('@supabase/supabase-js');

const app = express();
app.use(cors());
app.use(express.json());

const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

// --- 1. ОПТИМИЗИРОВАННАЯ ОПЛАТА ЗВЕЗДАМИ ---
app.post('/api/create_stars_pay', async (req, res) => {
    const { user_id, amount } = req.body;
    if (!BOT_TOKEN) return res.status(500).json({ error: "Config error" });

    try {
        // Добавляем тайм-аут для axios, чтобы не висело вечно
        const tgUrl = `https://api.telegram.org/bot${process.env.BOT_TOKEN}/createInvoiceLink`;
        
        const response = await axios.post(tgUrl, {
            title: "Пополнение баланса",
            description: `Покупка ${amount} звезд`,
            payload: String(user_id),
            provider_token: "",
            currency: "XTR",
            prices: [{ label: "Stars", amount: Math.floor(Number(amount)) }]
        }, { timeout: 5000 }); // Ждем ответа от ТГ не более 5 секунд

        if (response.data.ok) {
            return res.json({ pay_url: response.data.result });
        } else {
            return res.status(400).json({ error: response.data.description });
        }
    } catch (e) {
        console.error("Stars Pay Error:", e.message);
        return res.status(503).json({ error: "Telegram API timeout or error" });
    }
});

// --- 2. КРИПТО-ВЕБХУК (с использованием RPC) ---
// Рекомендую использовать SQL-функцию, которую мы создавали, чтобы избежать race condition
app.post('/api/crypto-webhook', async (req, res) => {
    const { status, payload, amount } = req.body;

    if (status === 'paid') {
        const userId = String(payload);
        const paidAmount = parseFloat(amount);

        // Используем RPC для атомарного прибавления (это быстрее и надежнее)
        const { error } = await supabase.rpc('increment_ton_balance', { 
            user_id_val: userId, 
            amount_val: paidAmount 
        });

        if (error) {
            console.error("Supabase Error:", error);
        }
    }
    // Всегда возвращаем 200, чтобы бот не слал повторы
    return res.status(200).send('OK');
});

module.exports = app;
