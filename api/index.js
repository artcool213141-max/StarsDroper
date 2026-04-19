const express = require('express');
const cors = require('cors');
const axios = require('axios');
const { createClient } = require('@supabase/supabase-js');

const app = express();

app.use(cors());
app.use(express.json());

// Настройки Supabase
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);
const BOT_TOKEN = process.env.BOT_TOKEN;

// 1. ПОЛУЧЕНИЕ БАЛАНСА (чтобы в приложении не было 0)
app.get('/api/get_balance/:user_id', async (req, res) => {
    const { user_id } = req.params;
    const { data, error } = await supabase
        .from('users') // Проверь, что таблица называется именно так
        .select('*')
        .eq('user_id', user_id)
        .single();
    
    if (error) return res.status(404).json({ error: "User not found" });
    res.json(data);
});

app.post('/api/create_stars_pay', async (req, res) => {
    const { user_id, amount } = req.body;
    try {
        const response = await axios.post(`https://api.telegram.org/bot${process.env.BOT_TOKEN}/createInvoiceLink`, {
            title: "Recharge Stars",
            description: `Buy ${amount} Stars`,
            payload: String(user_id),
            provider_token: "", 
            currency: "XTR",
            prices: [{ label: "Stars", amount: Math.floor(amount) }]
        });

        if (response.data.ok) {
            res.json({ pay_url: response.data.result });
        } else {
            console.error("TG Error:", response.data);
            res.status(400).json(response.data);
        }
    } catch (e) {
        console.error("Server Error:", e.response?.data || e.message);
        res.status(500).json({ error: "Ошибка на стороне сервера" });
    }
});

// 3. ТВOЙ КРИПТО-ВЕБХУК (Обновление базы при оплате через CryptoBot)
app.post('/api/crypto-webhook', async (req, res) => {
    const { status, payload, amount } = req.body;

    if (status === 'paid') {
        const userId = payload; 
        const paidAmount = parseFloat(amount);

        // Обновляем баланс в Supabase
        const { data: user } = await supabase.from('users').select('balance').eq('user_id', userId).single();
        const newBalance = (user?.balance || 0) + paidAmount;

        await supabase.from('users').update({ balance: newBalance }).eq('user_id', userId);
        console.log(`Баланс юзера ${userId} обновлен на ${paidAmount} TON`);
    }
    res.status(200).send('OK');
});

// ОБЯЗАТЕЛЬНО В КОНЦЕ
module.exports = app;
