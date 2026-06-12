const express = require('express');
const cors = require('cors');
const axios = require('axios');
const { createClient } = require('@supabase/supabase-js');

const app = express();

app.use(cors({ origin: true, credentials: true }));
app.use(express.json());

const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

const MY_CRYPTO_BOT_TOKEN = '595078:AARWA1nRE3vG9cCqQZclg8DgCJuga0msN9w';

// 1. ПОЛУЧЕНИЕ БАЛАНСА
app.get('/get_balance/:userId', async (req, res) => {
    try {
        const { userId } = req.params;
        const { data, error } = await supabase.from('users').select('balance, stars, tickets').eq('user_id', String(userId)).single();
        if (error && error.code === 'PGRST116') {
            const { data: newUser } = await supabase.from('users').insert([{ user_id: String(userId), balance: 0, stars: 0, tickets: 3 }]).select().single();
            return res.json(newUser);
        }
        return res.json(data);
    } catch (err) {
        return res.status(500).json({ error: err.message });
    }
});

// 2. ОПЛАТА ЗВЕЗДАМИ
app.post('/create_stars_pay', async (req, res) => {
    const { user_id, amount } = req.body;
    try {
        const response = await axios.post(`https://api.telegram.org/bot${process.env.BOT_TOKEN}/createInvoiceLink`, {
            title: "Пополнение баланса",
            description: `Покупка ${amount} звезд`,
            payload: String(user_id),
            currency: "XTR",
            prices: [{ label: "Stars", amount: Math.floor(Number(amount)) }]
        });
        return res.json({ pay_url: response.data.result });
    } catch (e) {
        return res.status(503).json({ error: "Telegram API error" });
    }
});

// 3. КРИПТО-ВЕБХУК
app.post('/crypto-webhook', async (req, res) => {
    if (req.body.status === 'paid') {
        await supabase.rpc('increment_ton_balance', { user_id_val: String(req.body.payload), amount_val: parseFloat(req.body.amount) });
    }
    return res.status(200).send('OK');
});

// 4. ЕДИНСТВЕННЫЙ РОУТ ДЛЯ CRYPTO PAY
app.post('/create_crypto_pay', async (req, res) => {
    const { user_id, amount } = req.body;
    try {
        const response = await axios.post('https://pay.crypt.bot/api/createInvoice', {
            asset: "TON",
            amount: String(amount),
            payload: String(user_id),
            description: "Пополнение баланса TON"
        }, {
            headers: { 'Crypto-Pay-API-Token': MY_CRYPTO_BOT_TOKEN }
        });
        return res.json({ pay_url: response.data.result.bot_invoice_url });
    } catch (e) {
        console.error("CRYPTO ERROR:", e.response?.data || e.message);
        return res.status(500).json({ error: "CryptoBot API Error", details: e.response?.data });
    }
});

module.exports = app;
