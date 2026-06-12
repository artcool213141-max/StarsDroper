const express = require('express');
const cors = require('cors');
const axios = require('axios');
const { createClient } = require('@supabase/supabase-js');

const app = express();
app.use(cors({ origin: true, credentials: true }));
app.use(express.json());

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);
const MY_CRYPTO_BOT_TOKEN = '595078:AARWA1nRE3vG9cCqQZclg8DgCJuga0msN9w'; // Убедись, что это API-токен!

// Роут для Крипто-бота (Оплата)
app.post('/create_crypto_pay', async (req, res) => {
    const { user_id, amount } = req.body;
    try {
        const response = await axios.post('https://pay.crypt.bot/api/createInvoice', {
            asset: "TON",
            amount: String(amount),
            payload: String(user_id),
            description: "Пополнение баланса TON"
        }, { headers: { 'Crypto-Pay-API-Token': MY_CRYPTO_BOT_TOKEN } });
        
        return res.json({ pay_url: response.data.result.bot_invoice_url });
    } catch (e) {
        console.error("CRYPTO ERROR:", e.response?.data || e.message);
        return res.status(500).json({ error: "API Error" });
    }
});

// ВЕБХУК — ТО, ЧТО ЗАЧИСЛЯЕТ ДЕНЬГИ
app.post('/crypto-webhook', async (req, res) => {
    // Проверка: бот прислал оплату?
    if (req.body.update_type === 'invoice_paid') {
        const payload = req.body.payload.payload; // Тут наш user_id
        const amount = req.body.payload.asset_amount;
        
        // Вызываем функцию в базе
        await supabase.rpc('increment_ton_balance', { 
            user_id_val: String(payload), 
            amount_val: parseFloat(amount) 
        });
    }
    return res.status(200).send('OK');
});

module.exports = app;
