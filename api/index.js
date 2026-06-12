const express = require('express');
const cors = require('cors');
const axios = require('axios');
const { createClient } = require('@supabase/supabase-js');

const app = express();

// Разрешаем CORS полностью, чтобы CORB не докапывался
app.use(cors({ origin: true, credentials: true }));
app.use(express.json());

const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

// --- 1. РОУТ ДЛЯ ПОЛУЧЕНИЯ БАЛАНСА (БЕЗ НЕГО ВСЁ ВИСИТ НА ЗАГРУЗКЕ) ---
app.get('/get_balance/:userId', async (req, res) => {
    try {
        const { userId } = req.params;
        
        // Запрос в Supabase. Убедись, что таблица называется именно 'users' (или поменяй название)
        const { data, error } = await supabase
            .from('users')
            .select('balance, stars, tickets')
            .eq('user_id', String(userId))
            .single();

        if (error && error.code === 'PGRST116') {
            // Если юзера еще нет в базе, регистрируем его с дефолтными балансами
            const { data: newUser, error: createError } = await supabase
                .from('users')
                .insert([{ user_id: String(userId), balance: 0, stars: 0, tickets: 3 }])
                .select()
                .single();
                
            if (createError) throw createError;
            return res.json(newUser);
        }

        if (error) throw error;
        return res.json(data);
    } catch (err) {
        console.error("Balance Route Error:", err.message);
        return res.status(500).json({ error: err.message });
    }
});

// --- 2. ОПЛАТА ЗВЕЗДАМИ ---
app.post('/create_stars_pay', async (req, res) => {
    const { user_id, amount } = req.body;
    
    if (!process.env.BOT_TOKEN) {
        return res.status(500).json({ error: "Config error: BOT_TOKEN missing" });
    }
    
    try {
        const tgUrl = `https://api.telegram.org/bot${process.env.BOT_TOKEN}/createInvoiceLink`;
        
        const response = await axios.post(tgUrl, {
            title: "Пополнение баланса",
            description: `Покупка ${amount} звезд`,
            payload: String(user_id),
            provider_token: "",
            currency: "XTR",
            prices: [{ label: "Stars", amount: Math.floor(Number(amount)) }]
        }, { timeout: 5000 });

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

// --- 3. КРИПТО-ВЕБХУК ---
app.post('/crypto-webhook', async (req, res) => {
    try {
        const { status, payload, amount } = req.body;

        if (status === 'paid') {
            const userId = String(payload);
            const paidAmount = parseFloat(amount);

            const { error } = await supabase.rpc('increment_ton_balance', { 
                user_id_val: userId, 
                amount_val: paidAmount 
            });

            if (error) console.error("Supabase Error:", error);
        }
    } catch (err) {
        console.error("Webhook Error:", err.message);
    }
    return res.status(200).send('OK');
});

// --- 4. СОЗДАНИЕ СЧЕТА В TON (CRYPTO BOT) ---
app.post('/create_crypto_pay', async (req, res) => {
    const { user_id, amount } = req.body;
    
    if (!process.env.CRYPTO_BOT_TOKEN) {
        return res.status(500).json({ error: "Config error: CRYPTO_BOT_TOKEN missing" });
    }
    
    try {
        // Стучимся в API Криптобота
        const cryptoUrl = `https://pay.crypton.sh/api/createInvoice`; // Для продакшена. Если тестнет, то testnet-pay.crypton.sh
        
        const response = await axios.post(cryptoUrl, {
            asset: "TON",                    // Валюта — строго TON
            amount: String(amount),          // Сумма пополнения (строкой)
            payload: String(user_id),        // Передаем ID юзера, чтобы поймать его в вебхуке
            description: "Пополнение баланса TON",
            allow_comments: false,
            allow_anonymous: false
        }, {
            headers: { 'Crypto-Pay-API-Token': process.env.CRYPTO_BOT_TOKEN },
            timeout: 5000
        });

        if (response.data && response.data.ok) {
            // Возвращаем фронтенду ссылку на оплату (bot_invoice_url)
            return res.json({ pay_url: response.data.result.bot_invoice_url });
        } else {
            return res.status(400).json({ error: response.data.error || "CryptoBot error" });
        }
    } catch (e) {
        console.error("Crypto Pay Invoice Error:", e.response?.data || e.message);
        return res.status(503).json({ error: "CryptoBot API error" });
    }
});

module.exports = app;
