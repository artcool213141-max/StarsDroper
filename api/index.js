const express = require('express'); // 1. Подключаем экспресс
const cors = require('cors');
const axios = require('axios');
const { createClient } = require('@supabase/supabase-js');

const app = express(); // 2. ВОТ ЭТОГО У ТЕБЯ НЕ ХВАТАЕТ (создаем app)

app.use(cors()); // Разрешаем запросы из браузера
app.use(express.json()); // Чтобы сервер понимал JSON в запросах

// Дальше идут твои настройки Supabase...
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);
// Обработка входящего уведомления об оплате
app.post('/api/crypto-webhook', async (req, res) => {
    const { status, payload, amount } = req.body;

    if (status === 'paid') {
        const userId = req.body.payload; // Мы вытаскиваем ID юзера, который платил
        const paidAmount = req.body.amount;

        console.log(`Успех! Юзер ${userId} оплатил ${paidAmount}`);

        // ТУТ ДОЛЖНА БЫТЬ ТВОЯ БАЗА ДАННЫХ
        // Если базы пока нет, деньги придут тебе в кошелек бота, 
        // но цифра в приложении сама не вырастет.
    }

    // Обязательно отвечаем боту, что получили сигнал
    res.status(200).send('OK');
});
