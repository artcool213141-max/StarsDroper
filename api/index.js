const express = require('express');
const cors = require('cors');
const axios = require('axios');
const { createClient } = require('@supabase/supabase-js');

const app = express();

app.use(cors());
app.use(express.json());

// ВСТАВЬ ТОКЕН НАПРЯМУЮ ДЛЯ ПРОВЕРКИ
const BOT_TOKEN = "8340303311:AAFoEqmKEOUN4kiOGn7ZEWy2K972-7pYMjo"; // Прямо сюда, в кавычках!

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

app.post('/api/create_stars_pay', async (req, res) => {
    const { user_id, amount } = req.body;
    try {
        // Используем константу BOT_TOKEN, которую мы объявили выше
        const url = `https://api.telegram.org/bot${BOT_TOKEN}/createInvoiceLink`;
        
        const response = await axios.post(url, {
            title: "Stars",
            description: "Top up",
            payload: String(user_id),
            provider_token: "", 
            currency: "XTR",
            prices: [{ label: "Stars", amount: Math.floor(Number(amount)) }]
        });

        if (response.data.ok) {
            res.json({ pay_url: response.data.result });
        } else {
            res.status(400).json(response.data);
        }
    } catch (e) {
        // Если упадет тут, мы увидим подробности
        console.error("FULL ERROR:", e.response?.data || e.message);
        res.status(500).json({ error: e.response?.data || e.message });
    }
});

app.post('/api/create_stars_pay', async (req, res) => {
    const { user_id, amount } = req.body;
    try {
        // Проверяем токен в логах (для отладки, потом удалишь)
        console.log("Использую токен:", process.env.BOT_TOKEN ? "Ок" : "ПУСТО!");

        const response = await axios.post(`https://api.telegram.org/bot${process.env.BOT_TOKEN}/createInvoiceLink`, {
            title: "Stars", // Коротко и ясно
            description: "Top up balance", 
            payload: String(user_id),
            provider_token: "", 
            currency: "XTR",
            prices: [{ 
                label: "Stars", 
                amount: Math.floor(Number(amount)) // Строго целое число
            }]
        });

        if (response.data.ok) {
            console.log("Ссылка создана успешно");
            res.json({ pay_url: response.data.result });
        } else {
            console.error("Ошибка от TG:", response.data);
            res.status(400).json(response.data);
        }
    } catch (e) {
        console.error("Ошибка запроса:", e.response?.data || e.message);
        res.status(500).json({ error: "Server error" });
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
