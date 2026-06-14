const express = require('express');
const axios = require('axios');
const app = express();

app.use(express.json());

const BOT_TOKEN = process.env.BOT_TOKEN; // Не забудь добавить в Vercel Settings!

app.post('/api/index.js', async (req, res) => {
    const { amount } = req.body;

    try {
        const response = await axios.post(`https://api.telegram.org/bot${BOT_TOKEN}/createInvoiceLink`, {
            title: "Пополнение баланса",
            description: "Покупка звезд в NowearSpin",
            payload: "stars_purchase",
            currency: "XTR",
            prices: [{ label: "XTR", amount: amount }]
        });

        if (response.data.ok) {
            res.json({ pay_url: response.data.result });
        } else {
            res.status(500).json({ error: response.data.description });
        }
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

module.exports = app;
